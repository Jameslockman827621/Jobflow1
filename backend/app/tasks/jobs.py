from app.tasks import celery_app
from app.scrapers import GreenhouseScraper, LeverScraper, WorkableScraper
from app.database import SessionLocal
from app.models.job import Job, JobSource
from datetime import datetime
from typing import List


@celery_app.task
def scrape_greenhouse_companies(company_subdomains: List[str]):
    """Scrape jobs from multiple Greenhouse companies"""
    scraper = GreenhouseScraper()
    db = SessionLocal()
    
    try:
        source, _ = db.query(JobSource).filter_by(name="greenhouse").first_or_create(
            defaults={"base_url": scraper.base_url}
        )
        
        for subdomain in company_subdomains:
            jobs = scraper.scrape_company_jobs(subdomain)
            # TODO: Save jobs to DB
            print(f"Scraped {len(jobs)} jobs from {subdomain}")
        
        source.last_scraped = datetime.utcnow()
        db.commit()
    finally:
        db.close()


@celery_app.task
def scrape_lever_companies(company_subdomains: List[str]):
    """Scrape jobs from multiple Lever companies"""
    scraper = LeverScraper()
    db = SessionLocal()
    
    try:
        source, _ = db.query(JobSource).filter_by(name="lever").first_or_create(
            defaults={"base_url": scraper.base_url}
        )
        
        for subdomain in company_subdomains:
            jobs = scraper.scrape_company_jobs(subdomain)
            # TODO: Save jobs to DB
            print(f"Scraped {len(jobs)} jobs from {subdomain}")
        
        source.last_scraped = datetime.utcnow()
        db.commit()
    finally:
        db.close()
