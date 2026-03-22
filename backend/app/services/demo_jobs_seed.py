"""
Curated demo jobs used when the database has no scraped results yet.
Disabled when settings.AUTO_SEED_DEMO_JOBS is False.
"""

from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.models.job import Job, JobSource


DEMO_JOBS: List[dict] = [
    {
        "title": "Software Engineer",
        "company": "Demo Tech Ltd",
        "location": "London, UK",
        "remote": True,
        "external_url": "https://example.com/jobs/demo-software-engineer",
        "external_id": "demo-se-1",
        "description": "Sample listing so you can try the dashboard before live scrapers return results.",
        "min_salary": 55000,
        "max_salary": 75000,
        "seniority": "mid",
    },
    {
        "title": "Senior Backend Developer",
        "company": "Sample SaaS Inc",
        "location": "Remote (UK)",
        "remote": True,
        "external_url": "https://example.com/jobs/demo-backend",
        "external_id": "demo-be-1",
        "description": "Python, FastAPI, PostgreSQL. Demo job for onboarding.",
        "min_salary": 70000,
        "max_salary": 95000,
        "seniority": "senior",
    },
    {
        "title": "Product Manager",
        "company": "Demo Product Co",
        "location": "Manchester, UK",
        "remote": False,
        "external_url": "https://example.com/jobs/demo-pm",
        "external_id": "demo-pm-1",
        "description": "B2B SaaS product management. Sample role.",
        "min_salary": 60000,
        "max_salary": 85000,
        "seniority": "mid",
    },
    {
        "title": "Data Analyst",
        "company": "Demo Analytics",
        "location": "Edinburgh, UK",
        "remote": True,
        "external_url": "https://example.com/jobs/demo-analyst",
        "external_id": "demo-da-1",
        "description": "SQL, dashboards, experimentation. Demo listing.",
        "min_salary": 45000,
        "max_salary": 60000,
        "seniority": "mid",
    },
    {
        "title": "Frontend Engineer (React)",
        "company": "Sample Web Studio",
        "location": "Bristol, UK",
        "remote": True,
        "external_url": "https://example.com/jobs/demo-fe",
        "external_id": "demo-fe-1",
        "description": "React, TypeScript, design systems. Demo job.",
        "min_salary": 50000,
        "max_salary": 70000,
        "seniority": "mid",
    },
]


def ensure_demo_jobs(db: Session) -> int:
    """Insert demo jobs if none exist. Returns number of jobs inserted."""
    from app.core.config import settings

    if not settings.AUTO_SEED_DEMO_JOBS:
        return 0

    existing = db.query(Job).count()
    if existing > 0:
        return 0

    source = db.query(JobSource).filter_by(name="curated").first()
    if not source:
        source = JobSource(
            name="curated",
            base_url="https://jobscale.local",
            is_active=True,
        )
        db.add(source)
        db.commit()
        db.refresh(source)

    now = datetime.utcnow()
    inserted = 0
    for row in DEMO_JOBS:
        job = Job(
            source_id=source.id,
            external_id=row["external_id"],
            external_url=row["external_url"],
            title=row["title"],
            company=row["company"],
            location=row["location"],
            remote=row["remote"],
            hybrid=False,
            description=row["description"],
            seniority=row.get("seniority"),
            min_salary=row.get("min_salary"),
            max_salary=row.get("max_salary"),
            scraped_at=now,
            posted_date=now,
            is_active=True,
        )
        db.add(job)
        inserted += 1

    db.commit()
    return inserted
