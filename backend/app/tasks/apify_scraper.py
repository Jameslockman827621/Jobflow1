"""
Celery tasks for Apify LinkedIn Jobs Scraper

Scheduled to run daily via Celery Beat.
"""

from app.tasks import celery_app
from app.database import SessionLocal
from app.models.job import Job, JobSource
from app.scrapers.apify_linkedin import ApifyLinkedInScraper
from app.core.config import settings
from datetime import datetime
from typing import List, Dict


def _run_async(coro):
    """Helper to run async code in sync Celery task"""
    import asyncio
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task
def scrape_linkedin_jobs(search_configs: List[Dict]):
    """
    Scrape LinkedIn jobs for multiple search queries
    
    Args:
        search_configs: List of search configurations
        Example:
        [
            {
                "keywords": "Software Engineer",
                "location": "United Kingdom",
                "max_jobs": 100
            },
            {
                "keywords": "Python Developer",
                "location": "London",
                "max_jobs": 50
            }
        ]
    """
    if not settings.APIFY_API_KEY:
        print("❌ APIFY_API_KEY not configured, skipping LinkedIn scrape")
        return {"status": "skipped", "reason": "no_api_key"}
    
    scraper = ApifyLinkedInScraper(api_key=settings.APIFY_API_KEY)
    db = SessionLocal()
    
    try:
        # Get or create JobSource
        source = db.query(JobSource).filter_by(name="apify_linkedin").first()
        if not source:
            source = JobSource(
                name="apify_linkedin",
                base_url="https://www.linkedin.com/jobs",
                description="LinkedIn Jobs via Apify API"
            )
            db.add(source)
            db.commit()
        
        total_jobs = 0
        failed_searches = []
        
        for config in search_configs:
            try:
                print(f"🔍 Searching: {config.get('keywords', '')} in {config.get('location', '')}")
                
                jobs = _run_async(scraper.search_jobs(
                    keywords=config.get("keywords", ""),
                    location=config.get("location", ""),
                    max_jobs=config.get("max_jobs", 100),
                    date_posted=config.get("date_posted", "month"),
                    job_type=config.get("job_type", "fulltime"),
                    remote=config.get("remote", True),
                ))
                
                total_jobs += len(jobs)
                print(f"  ✅ Found {len(jobs)} jobs")
                
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
                    db.merge(job)  # Upsert by external_id
                
                db.commit()
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                failed_searches.append({
                    "config": config,
                    "error": str(e)
                })
                continue
        
        source.last_scraped = datetime.utcnow()
        db.commit()
        
        return {
            "status": "completed",
            "total_jobs": total_jobs,
            "searches_completed": len(search_configs) - len(failed_searches),
            "failed_searches": failed_searches
        }
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task
def scrape_linkedin_daily():
    """
    Daily LinkedIn job scrape with predefined search queries
    
    Runs every day at 6 AM via Celery Beat.
    """
    # Default search configurations
    search_configs = [
        # General tech roles - UK
        {"keywords": "Software Engineer", "location": "United Kingdom", "max_jobs": 100},
        {"keywords": "Python Developer", "location": "United Kingdom", "max_jobs": 50},
        {"keywords": "Java Developer", "location": "United Kingdom", "max_jobs": 50},
        {"keywords": "Frontend Developer", "location": "United Kingdom", "max_jobs": 50},
        {"keywords": "Backend Developer", "location": "United Kingdom", "max_jobs": 50},
        {"keywords": "Full Stack Developer", "location": "United Kingdom", "max_jobs": 50},
        {"keywords": "DevOps Engineer", "location": "United Kingdom", "max_jobs": 50},
        {"keywords": "Data Engineer", "location": "United Kingdom", "max_jobs": 50},
        {"keywords": "Machine Learning Engineer", "location": "United Kingdom", "max_jobs": 50},
        
        # London specific
        {"keywords": "Software Engineer", "location": "London", "max_jobs": 100},
        {"keywords": "Python Developer", "location": "London", "max_jobs": 50},
        {"keywords": "Data Scientist", "location": "London", "max_jobs": 50},
        
        # Senior roles
        {"keywords": "Senior Software Engineer", "location": "United Kingdom", "max_jobs": 50},
        {"keywords": "Staff Engineer", "location": "United Kingdom", "max_jobs": 30},
        {"keywords": "Principal Engineer", "location": "United Kingdom", "max_jobs": 30},
        
        # Remote
        {"keywords": "Software Engineer", "location": "United Kingdom", "max_jobs": 50, "remote": True},
    ]
    
    return scrape_linkedin_jobs.delay(search_configs)
