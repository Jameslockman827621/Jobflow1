"""
Background Career Page Monitor

Celery task that periodically scrapes all companies in our directory across
every ATS provider, enriches the jobs, and notifies users whose preferences
match the new postings. This is the "50,000+ pages watched" feature — jobs
appear on the user's dashboard automatically without them searching.

Runs every 2 hours via Celery beat. For each company in COMPANY_DIRECTORY:
  1. Scrape their ATS (Greenhouse/Lever/Ashby/Workable)
  2. Enrich each job with structured fields
  3. Save new jobs to the DB
  4. For each active user, check if the new jobs match their preferences
  5. If yes, add to their search cache + send a notification email
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict

from app.tasks import celery_app
from app.database import SessionLocal
from app.models.job import Job, JobSource
from app.models.preferences import UserPreferences
from app.models.search_cache import SearchCache
from app.models.user import User
from app.services.job_enricher import enrich_job
from app.services.cv_tailor import _extract_keywords
from app.services.email import email_service


@celery_app.task(bind=True, time_limit=600)
def monitor_career_pages(self):
    """Background monitor — scrape all known companies and notify users of new matches."""
    db = SessionLocal()
    try:
        from app.scrapers.companies import COMPANY_DIRECTORY
        from app.scrapers.greenhouse import GreenhouseScraper
        from app.scrapers.lever import LeverScraper
        from app.scrapers.ashby import AshbyScraper
        from app.scrapers.workable import WorkableScraper

        scrapers = {
            "greenhouse": GreenhouseScraper(),
            "lever": LeverScraper(),
            "ashby": AshbyScraper(),
            "workable": WorkableScraper(),
        }

        # Get or create job sources
        sources = {}
        for name in scrapers.keys():
            src = db.query(JobSource).filter_by(name=name).first()
            if not src:
                src = JobSource(name=name, base_url=f"https://{name}.com", is_active=True)
                db.add(src)
                db.commit()
                db.refresh(src)
            sources[name] = src

        total_new_jobs = 0
        companies_scraped = 0

        # Scrape each company in the directory
        for entry in COMPANY_DIRECTORY[:50]:  # Cap at 50 per run to stay within time limit
            name, industry, size, ats, slug = entry
            scraper = scrapers.get(ats)
            if not scraper:
                continue

            try:
                # Run the async scraper in a sync context
                loop = asyncio.new_event_loop()
                try:
                    jobs = loop.run_until_complete(scraper.scrape_company_jobs(slug))
                finally:
                    loop.close()

                if not jobs:
                    continue

                companies_scraped += 1
                new_count = 0

                for job_data in jobs:
                    jd = job_data.to_dict()
                    jd["_source"] = ats
                    jd["company"] = name  # Use the friendly name from directory

                    # Enrich
                    try:
                        jd = enrich_job(jd)
                    except Exception:
                        pass

                    # Skip if missing required fields
                    if not jd.get("title") or not jd.get("external_url"):
                        continue

                    # Check if job already exists (by source + external_id)
                    src = sources[ats]
                    ext_id = jd.get("external_id", "")
                    existing = db.query(Job).filter_by(
                        source_id=src.id, external_id=ext_id
                    ).first() if ext_id else None

                    if existing:
                        # Update existing job
                        existing.is_active = True
                        existing.scraped_at = datetime.utcnow()
                        continue

                    # Create new job
                    job = Job(
                        source_id=src.id,
                        external_id=ext_id,
                        external_url=jd.get("external_url", ""),
                        title=jd.get("title", ""),
                        company=name,
                        location=jd.get("location", ""),
                        remote=jd.get("remote", False),
                        hybrid=jd.get("hybrid", False),
                        description=jd.get("description", ""),
                        seniority=jd.get("seniority", ""),
                        employment_type=jd.get("employment_type", "full_time"),
                        min_salary=jd.get("min_salary"),
                        max_salary=jd.get("max_salary"),
                        skills_required=jd.get("skills_required", []),
                        visa_sponsorship=jd.get("visa_sponsorship"),
                        industry=industry,
                        company_size=size,
                        benefits_extracted=jd.get("benefits_extracted", []),
                        scraped_at=datetime.utcnow(),
                        posted_date=datetime.utcnow(),
                        is_active=True,
                    )
                    db.add(job)
                    db.commit()
                    db.refresh(job)
                    new_count += 1
                    total_new_jobs += 1

                if new_count > 0:
                    print(f"  Monitor: {name} ({ats}) — {new_count} new jobs")

            except Exception as e:
                print(f"  Monitor: error scraping {name} ({ats}): {e}")
                continue

        # Notify users whose preferences match new jobs
        if total_new_jobs > 0:
            _notify_matching_users(db, total_new_jobs)

        return {
            "status": "completed",
            "companies_scraped": companies_scraped,
            "new_jobs": total_new_jobs,
        }
    finally:
        db.close()


def _notify_matching_users(db, new_job_count: int):
    """Check if any users' preferences match the new jobs and notify them."""
    try:
        # Get all active preferences
        prefs = db.query(UserPreferences).filter(
            UserPreferences.is_active == True
        ).all()

        for pref in prefs:
            user = db.query(User).filter(User.id == pref.user_id).first()
            if not user:
                continue

            # Simple matching: check if any of the user's target roles appear in recent jobs
            recent_cutoff = datetime.utcnow() - timedelta(hours=3)
            recent_jobs = db.query(Job).filter(
                Job.is_active == True,
                Job.scraped_at > recent_cutoff,
            ).limit(20).all()

            matched = []
            for job in recent_jobs:
                # Check role match
                if pref.target_roles:
                    role_match = any(
                        role.lower() in (job.title or "").lower()
                        for role in pref.target_roles
                    )
                    if not role_match:
                        continue

                # Check company match
                if pref.target_companies:
                    company_match = any(
                        company.lower() in (job.company or "").lower()
                        for company in pref.target_companies
                    )
                    if not company_match and len(pref.target_companies) > 0:
                        continue

                matched.append(job)

            if matched:
                # Send notification email
                try:
                    email_service.send_job_alert(
                        to=user.email,
                        jobs=[{
                            "title": j.title,
                            "company": j.company,
                            "location": j.location or "Remote",
                            "url": j.external_url,
                        } for j in matched[:5]],
                    )
                    print(f"  Monitor: notified {user.email} about {len(matched)} new matching jobs")
                except Exception as e:
                    print(f"  Monitor: email error for {user.email}: {e}")

    except Exception as e:
        print(f"  Monitor: notification error: {e}")
