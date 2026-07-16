"""Company directory + monitoring coverage API."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.company import MonitoredCompany
from app.models.user import User
from app.scrapers.companies import DIRECTORY_CAPACITY_TARGET, all_seed_companies
from app.services.company_directory import bulk_import, list_companies, seed_monitored_companies
from app.services.company_discovery import discover_companies
from app.services.proxy_pool import pool_status

router = APIRouter()


class CompanyImportItem(BaseModel):
    name: Optional[str] = None
    slug: str
    ats_type: str
    career_url: Optional[str] = None
    priority: Optional[str] = "cold"
    industry: Optional[str] = None
    country: Optional[str] = "US"


class BulkImportRequest(BaseModel):
    companies: List[CompanyImportItem] = Field(default_factory=list)


@router.post("/seed")
async def seed_directory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Seed/refresh the monitored company directory from curated ATS lists."""
    return seed_monitored_companies(db)


@router.get("")
async def get_companies(
    ats_type: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_companies(
        db,
        ats_type=ats_type,
        priority=priority,
        limit=min(limit, 500),
        offset=max(offset, 0),
    )


@router.get("/coverage")
async def coverage_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = db.query(MonitoredCompany).filter(MonitoredCompany.is_active.is_(True)).count()
    by_ats = {}
    by_priority = {}
    for row in db.query(MonitoredCompany).filter(MonitoredCompany.is_active.is_(True)).all():
        by_ats[row.ats_type] = by_ats.get(row.ats_type, 0) + 1
        by_priority[row.priority] = by_priority.get(row.priority, 0) + 1
    return {
        "monitored_career_pages": total,
        "capacity_target": DIRECTORY_CAPACITY_TARGET,
        "coverage_pct": round((total / DIRECTORY_CAPACITY_TARGET) * 100, 3) if DIRECTORY_CAPACITY_TARGET else 0,
        "by_ats": by_ats,
        "by_priority": by_priority,
        "proxy_pool": pool_status(),
        "monitoring": {
            "hot_interval_seconds": 60,
            "warm_interval_minutes": 15,
            "cold_interval_hours": 2,
            "mode": "priority_polling",
        },
    }


@router.post("/import")
async def import_companies(
    body: BulkImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not body.companies:
        raise HTTPException(status_code=400, detail="No companies provided")
    if len(body.companies) > 5000:
        raise HTTPException(status_code=400, detail="Max 5000 companies per import")
    return bulk_import(db, [c.model_dump() for c in body.companies])


@router.post("/discover")
async def discover_live_boards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Probe public ATS APIs and import verified career pages into the directory."""
    seed = seed_monitored_companies(db)
    discovery = await discover_companies()
    payload = [
        {k: v for k, v in c.items() if k != "job_count"}
        for c in discovery["companies"]
    ]
    imported = bulk_import(db, payload)
    for c in discovery["companies"]:
        row = (
            db.query(MonitoredCompany)
            .filter(MonitoredCompany.ats_type == c["ats_type"], MonitoredCompany.slug == c["slug"])
            .first()
        )
        if row:
            row.last_job_count = c.get("job_count") or 0
            row.priority = c.get("priority") or row.priority
            row.is_active = True
    db.commit()
    total = db.query(MonitoredCompany).filter(MonitoredCompany.is_active.is_(True)).count()
    return {
        "seed": seed,
        "discovery": {
            "probed": discovery["probed"],
            "found": discovery["found"],
            "by_ats": discovery["by_ats"],
            "estimated_jobs": discovery["estimated_jobs"],
        },
        "imported": imported,
        "monitored_total": total,
        "seed_catalog_size": len(all_seed_companies()),
    }
