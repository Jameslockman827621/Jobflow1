import asyncio
from app.tasks import celery_app
from app.scrapers import GreenhouseScraper, LeverScraper
from app.database import SessionLocal
from app.models.job import Job, JobSource
from app.scrapers.base import JobData
from datetime import datetime, timedelta
from typing import List, Tuple


def _run_async(coro):
    """Helper to run async code in sync Celery task"""
    return asyncio.get_event_loop().run_until_complete(coro)


def _check_duplicate(db: SessionLocal, source_id: int, job_data: JobData) -> Tuple[bool, str]:
    """
    Check if a job is a duplicate before inserting.
    
    Checks:
    1. Same source + external_id (fastest)
    2. Same external_url (cross-source)
    3. Same company + title + location (fuzzy)
    
    Returns:
        Tuple of (is_duplicate, reason)
    """
    # Check 1: Same source + external_id
    if job_data.external_id:
        existing = db.query(Job).filter_by(
            source_id=source_id,
            external_id=job_data.external_id,
            is_active=True
        ).first()
        
        if existing:
            return True, f"Duplicate source ID (job #{existing.id})"
    
    # Check 2: Same URL (cross-source deduplication)
    if job_data.external_url:
        existing = db.query(Job).filter_by(
            external_url=job_data.external_url,
            is_active=True
        ).first()
        
        if existing:
            return True, f"Duplicate URL (job #{existing.id})"
    
    # Check 3: Same company + normalized title + location
    # Only for jobs from different sources (already checked source_id above)
    existing = db.query(Job).filter(
        Job.company.ilike(f"%{job_data.company}%"),
        Job.is_active == True
    ).limit(50).all()
    
    if existing:
        # Normalize title for comparison
        import re
        title_norm = re.sub(r'[^\w\s]', ' ', job_data.title.lower()).strip()
        title_norm = ' '.join(sorted(title_norm.split()))
        
        for job in existing:
            job_title_norm = re.sub(r'[^\w\s]', ' ', job.title.lower()).strip()
            job_title_norm = ' '.join(sorted(job_title_norm.split()))
            
            # Check if titles are similar (within same company and location)
            if title_norm == job_title_norm:
                if job.location and job_data.location:
                    if job.location.lower() in job_data.location.lower() or job_data.location.lower() in job.location.lower():
                        return True, f"Duplicate company/title/location (job #{job.id})"
    
    return False, ""


@celery_app.task
def scrape_greenhouse_companies(company_subdomains: List[str]):
    """Scrape jobs from multiple Greenhouse companies"""
    scraper = GreenhouseScraper()
    db = SessionLocal()
    
    try:
        source = db.query(JobSource).filter_by(name="greenhouse").first()
        if not source:
            source = JobSource(name="greenhouse", base_url=scraper.base_url)
            db.add(source)
            db.commit()
        
        total_jobs = 0
        for subdomain in company_subdomains:
            try:
                jobs = _run_async(scraper.scrape_company_jobs(subdomain))
                total_jobs += len(jobs)
                print(f"  {subdomain}: {len(jobs)} jobs")
                
                # Save jobs to DB with deduplication
                saved = 0
                skipped = 0
                
                for job_data in jobs:
                    # Check for duplicates before inserting
                    is_dup, reason = _check_duplicate(db, source.id, job_data)
                    
                    if is_dup:
                        skipped += 1
                        continue
                    
                    job = Job(
                        source_id=source.id,
                        external_id=job_data.external_id,
                        external_url=job_data.external_url,
                        title=job_data.title,
                        company=job_data.company,
                        location=job_data.location,
                        remote=job_data.remote,
                        hybrid=job_data.hybrid,
                        description=job_data.description,
                        department=job_data.department,
                        seniority=job_data.seniority,
                        min_salary=job_data.min_salary,
                        max_salary=job_data.max_salary,
                        scraped_at=datetime.utcnow(),
                        posted_date=job_data.posted_date,
                    )
                    db.merge(job)  # Upsert by external_id
                    saved += 1
                
                db.commit()
                print(f"    Saved: {saved}, Skipped (duplicates): {skipped}")
            except Exception as e:
                print(f"Error scraping {subdomain}: {e}")
                continue
        
        source.last_scraped = datetime.utcnow()
        db.commit()
        
        return {"status": "completed", "total_jobs": total_jobs}
    finally:
        db.close()


@celery_app.task
def scrape_lever_companies(company_subdomains: List[str]):
    """Scrape jobs from multiple Lever companies"""
    scraper = LeverScraper()
    db = SessionLocal()
    
    try:
        source = db.query(JobSource).filter_by(name="lever").first()
        if not source:
            source = JobSource(name="lever", base_url=scraper.base_url)
            db.add(source)
            db.commit()
        
        total_jobs = 0
        for subdomain in company_subdomains:
            try:
                jobs = _run_async(scraper.scrape_company_jobs(subdomain))
                total_jobs += len(jobs)
                print(f"  {subdomain}: {len(jobs)} jobs")
                
                # Save jobs to DB
                for job_data in jobs:
                    job = Job(
                        source_id=source.id,
                        external_id=job_data.external_id,
                        external_url=job_data.external_url,
                        title=job_data.title,
                        company=job_data.company,
                        location=job_data.location,
                        remote=job_data.remote,
                        hybrid=job_data.hybrid,
                        description=job_data.description,
                        department=job_data.department,
                        seniority=job_data.seniority,
                        min_salary=job_data.min_salary,
                        max_salary=job_data.max_salary,
                        scraped_at=datetime.utcnow(),
                        posted_date=job_data.posted_date,
                    )
                    db.merge(job)
                
                db.commit()
            except Exception as e:
                print(f"Error scraping {subdomain}: {e}")
                continue
        
        source.last_scraped = datetime.utcnow()
        db.commit()
        
        return {"status": "completed", "total_jobs": total_jobs}
    finally:
        db.close()


@celery_app.task
def cleanup_old_jobs():
    """Remove jobs older than 90 days or marked inactive"""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=90)
        
        # Delete old jobs
        deleted = db.query(Job).filter(
            Job.scraped_at < cutoff
        ).delete()
        
        # Mark very old jobs as inactive instead of deleting
        very_old = datetime.utcnow() - timedelta(days=180)
        db.query(Job).filter(
            Job.scraped_at < very_old,
            Job.is_active == True
        ).update({"is_active": False})
        
        db.commit()
        print(f"Cleaned up {deleted} old jobs")
        return {"status": "completed", "deleted": deleted}
    finally:
        db.close()


@celery_app.task
def recalculate_all_matches():
    """Recalculate match scores for all user-job combinations"""
    from app.services.matching import JobMatcher
    from app.models.profile import UserProfile
    
    db = SessionLocal()
    try:
        profiles = db.query(UserProfile).all()
        jobs = db.query(Job).filter(Job.is_active == True).all()
        
        total_updates = 0
        for profile in profiles:
            matcher = JobMatcher(db)
            for job in jobs:
                score = matcher.calculate_match_score(profile, job)
                job.match_score = score
                total_updates += 1
        
        db.commit()
        print(f"Recalculated {total_updates} match scores")
        return {"status": "completed", "updates": total_updates}
    finally:
        db.close()
