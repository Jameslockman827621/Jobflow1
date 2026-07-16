"""
Near-real-time company monitoring tasks.

Priority tiers:
- hot: every ~30–60s (beat) — closest practical equivalent to "seconds after posting"
- warm: every 15 minutes
- cold: every 2 hours
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import List

from app.database import SessionLocal
from app.models.company import MonitoredCompany
from app.models.job import Job, JobSource
from app.scrapers.ashby import AshbyScraper
from app.scrapers.base import JobData
from app.scrapers.greenhouse import GreenhouseScraper
from app.scrapers.lever import LeverScraper
from app.scrapers.workable import WorkableScraper
from app.services.company_directory import companies_by_priority, mark_scraped, seed_monitored_companies
from app.services.proxy_pool import fingerprint_headers, httpx_proxies
from app.tasks import celery_app


def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.run(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def _get_scraper(ats_type: str):
    if ats_type == "greenhouse":
        return GreenhouseScraper()
    if ats_type == "lever":
        return LeverScraper()
    if ats_type == "workable":
        return WorkableScraper()
    if ats_type == "ashby":
        return AshbyScraper()
    return None


def _ensure_source(db, name: str, base_url: str = "") -> JobSource:
    source = db.query(JobSource).filter_by(name=name).first()
    if not source:
        source = JobSource(name=name, base_url=base_url)
        db.add(source)
        db.commit()
        db.refresh(source)
    return source


def _persist_jobs(db, source: JobSource, jobs: List[JobData]) -> int:
    saved = 0
    for job_data in jobs:
        if job_data.external_id:
            existing = db.query(Job).filter_by(
                source_id=source.id,
                external_id=job_data.external_id,
                is_active=True,
            ).first()
            if existing:
                continue
        if job_data.external_url:
            existing = db.query(Job).filter_by(
                external_url=job_data.external_url,
                is_active=True,
            ).first()
            if existing:
                continue
        db.add(
            Job(
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
                is_active=True,
            )
        )
        saved += 1
    if saved:
        db.commit()
    return saved


def _scrape_priority(priority: str, limit: int = 50) -> dict:
    db = SessionLocal()
    try:
        # Auto-seed empty directory so first beat run works
        if db.query(MonitoredCompany).count() == 0:
            seed_monitored_companies(db)

        companies = companies_by_priority(db, priority, limit=limit)
        totals = {"companies": 0, "jobs_found": 0, "jobs_saved": 0, "failures": 0, "priority": priority}

        for company in companies:
            scraper = _get_scraper(company.ats_type)
            if not scraper:
                continue
            # Apply fingerprint headers / proxy for non-API HTML scrapers
            try:
                scraper.headers = fingerprint_headers()
            except Exception:
                pass

            started = time.time()
            try:
                jobs = _run_async(scraper.scrape_company_jobs(company.slug))
                source = _ensure_source(db, company.ats_type, getattr(scraper, "base_url", ""))
                saved = _persist_jobs(db, source, jobs)
                elapsed_ms = (time.time() - started) * 1000
                mark_scraped(db, company, len(jobs), elapsed_ms=elapsed_ms, failed=False)
                db.commit()
                totals["companies"] += 1
                totals["jobs_found"] += len(jobs)
                totals["jobs_saved"] += saved
            except Exception as exc:
                mark_scraped(db, company, 0, failed=True)
                db.commit()
                totals["failures"] += 1
                print(f"Monitor scrape failed {company.ats_type}/{company.slug}: {exc}")

        return totals
    finally:
        db.close()


@celery_app.task(name="app.tasks.monitoring.monitor_hot_companies")
def monitor_hot_companies():
    """Near-real-time scrape for hot career pages."""
    return _scrape_priority("hot", limit=40)


@celery_app.task(name="app.tasks.monitoring.monitor_warm_companies")
def monitor_warm_companies():
    return _scrape_priority("warm", limit=80)


@celery_app.task(name="app.tasks.monitoring.monitor_cold_companies")
def monitor_cold_companies():
    return _scrape_priority("cold", limit=120)


@celery_app.task(name="app.tasks.monitoring.seed_company_directory")
def seed_company_directory_task():
    db = SessionLocal()
    try:
        return seed_monitored_companies(db)
    finally:
        db.close()
