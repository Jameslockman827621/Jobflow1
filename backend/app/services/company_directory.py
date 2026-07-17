"""
Company directory seeding + monitoring helpers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.company import MonitoredCompany
from app.scrapers.companies import (
    ASHBY_COMPANIES,
    DIRECTORY_CAPACITY_TARGET,
    GREENHOUSE_COMPANIES,
    LEVER_COMPANIES,
    WORKABLE_COMPANIES,
    all_seed_companies,
)


def seed_monitored_companies(db: Session) -> Dict:
    created = 0
    updated = 0
    for row in all_seed_companies():
        existing = (
            db.query(MonitoredCompany)
            .filter(
                MonitoredCompany.ats_type == row["ats_type"],
                MonitoredCompany.slug == row["slug"],
            )
            .first()
        )
        if existing:
            existing.name = row["name"]
            existing.career_url = row.get("career_url")
            existing.priority = row.get("priority") or existing.priority
            existing.is_active = True
            updated += 1
        else:
            db.add(
                MonitoredCompany(
                    name=row["name"],
                    slug=row["slug"],
                    ats_type=row["ats_type"],
                    career_url=row.get("career_url"),
                    priority=row.get("priority") or "cold",
                    is_active=True,
                )
            )
            created += 1
    db.commit()
    total = db.query(MonitoredCompany).count()
    return {
        "created": created,
        "updated": updated,
        "total": total,
        "capacity_target": DIRECTORY_CAPACITY_TARGET,
        "seed_breakdown": {
            "greenhouse": len(GREENHOUSE_COMPANIES),
            "lever": len(LEVER_COMPANIES),
            "workable": len(WORKABLE_COMPANIES),
            "ashby": len(ASHBY_COMPANIES),
        },
    }


def list_companies(
    db: Session,
    ats_type: Optional[str] = None,
    priority: Optional[str] = None,
    active_only: bool = True,
    limit: int = 100,
    offset: int = 0,
) -> Dict:
    q = db.query(MonitoredCompany)
    if active_only:
        q = q.filter(MonitoredCompany.is_active.is_(True))
    if ats_type:
        q = q.filter(MonitoredCompany.ats_type == ats_type)
    if priority:
        q = q.filter(MonitoredCompany.priority == priority)
    total = q.count()
    rows = q.order_by(MonitoredCompany.priority.asc(), MonitoredCompany.name.asc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "capacity_target": DIRECTORY_CAPACITY_TARGET,
        "companies": [
            {
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "ats_type": c.ats_type,
                "priority": c.priority,
                "career_url": c.career_url,
                "last_scraped_at": c.last_scraped_at.isoformat() if c.last_scraped_at else None,
                "last_job_count": c.last_job_count,
                "is_active": c.is_active,
            }
            for c in rows
        ],
    }


def companies_by_priority(db: Session, priority: str, limit: int = 200) -> List[MonitoredCompany]:
    from sqlalchemy import nullsfirst

    return (
        db.query(MonitoredCompany)
        .filter(MonitoredCompany.is_active.is_(True), MonitoredCompany.priority == priority)
        .order_by(nullsfirst(MonitoredCompany.last_scraped_at.asc()))
        .limit(limit)
        .all()
    )


def mark_scraped(db: Session, company: MonitoredCompany, job_count: int, elapsed_ms: Optional[float] = None, failed: bool = False):
    company.last_scraped_at = datetime.utcnow()
    company.last_job_count = job_count
    if failed:
        company.scrape_failures = (company.scrape_failures or 0) + 1
    else:
        company.scrape_failures = 0
    if elapsed_ms is not None:
        company.avg_scrape_ms = elapsed_ms
    db.add(company)


def bulk_import(db: Session, companies: List[Dict]) -> Dict:
    created = 0
    skipped = 0
    for row in companies:
        slug = (row.get("slug") or "").strip().lower()
        ats = (row.get("ats_type") or "").strip().lower()
        if not slug or not ats:
            skipped += 1
            continue
        exists = (
            db.query(MonitoredCompany)
            .filter(MonitoredCompany.ats_type == ats, MonitoredCompany.slug == slug)
            .first()
        )
        if exists:
            skipped += 1
            continue
        db.add(
            MonitoredCompany(
                name=row.get("name") or slug.title(),
                slug=slug,
                ats_type=ats,
                career_url=row.get("career_url"),
                priority=row.get("priority") or "cold",
                industry=row.get("industry"),
                country=row.get("country") or "US",
                is_active=True,
            )
        )
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped, "total": db.query(MonitoredCompany).count()}
