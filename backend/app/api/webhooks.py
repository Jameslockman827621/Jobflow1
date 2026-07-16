"""External job ingest webhooks."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.models.company import MonitoredCompany
from app.models.job import Job, JobSource

router = APIRouter()


class WebhookJobItem(BaseModel):
    title: str
    external_id: str
    external_url: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None


class JobsWebhookPayload(BaseModel):
    ats_type: str
    company_slug: str
    jobs: List[WebhookJobItem] = Field(default_factory=list)


def _check_webhook_secret(x_jobscale_webhook_secret: Optional[str]) -> None:
    expected = (settings.WEBHOOK_SECRET or "").strip()
    if not expected:
        # Secret unset → allow in non-production for local/dev ingest
        if settings.ENVIRONMENT.lower() == "production":
            raise HTTPException(status_code=503, detail="WEBHOOK_SECRET not configured")
        return
    if not x_jobscale_webhook_secret or x_jobscale_webhook_secret != expected:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")


def _ensure_source(db: Session, ats_type: str) -> JobSource:
    source = db.query(JobSource).filter_by(name=ats_type).first()
    if not source:
        source = JobSource(name=ats_type, base_url="")
        db.add(source)
        db.commit()
        db.refresh(source)
    return source


@router.post("/jobs")
async def ingest_jobs_webhook(
    payload: JobsWebhookPayload,
    db: Session = Depends(get_db),
    x_jobscale_webhook_secret: Optional[str] = Header(None, alias="X-JobScale-Webhook-Secret"),
):
    """
    Upsert jobs from an external scraper / partner.

    Body: {ats_type, company_slug, jobs:[{title, external_id, external_url, location, description}]}
    Auth: optional X-JobScale-Webhook-Secret matching settings.WEBHOOK_SECRET
    """
    _check_webhook_secret(x_jobscale_webhook_secret)

    ats_type = (payload.ats_type or "").strip().lower()
    slug = (payload.company_slug or "").strip().lower()
    if not ats_type or not slug:
        raise HTTPException(status_code=400, detail="ats_type and company_slug are required")

    source = _ensure_source(db, ats_type)
    created = 0
    updated = 0

    for item in payload.jobs:
        ext_id = (item.external_id or "").strip()
        if not ext_id:
            continue
        existing = (
            db.query(Job)
            .filter(
                Job.source_id == source.id,
                Job.external_id == ext_id,
            )
            .first()
        )
        loc = item.location or ""
        loc_lower = loc.lower()
        if existing:
            existing.title = item.title
            existing.company = slug
            existing.location = loc
            existing.external_url = item.external_url or existing.external_url
            existing.description = item.description or existing.description
            existing.remote = "remote" in loc_lower
            existing.hybrid = "hybrid" in loc_lower
            existing.scraped_at = datetime.utcnow()
            existing.is_active = True
            updated += 1
        else:
            db.add(
                Job(
                    source_id=source.id,
                    external_id=ext_id,
                    external_url=item.external_url,
                    title=item.title,
                    company=slug,
                    location=loc,
                    description=item.description or "",
                    remote="remote" in loc_lower,
                    hybrid="hybrid" in loc_lower,
                    scraped_at=datetime.utcnow(),
                    is_active=True,
                )
            )
            created += 1

    # Bump monitored company last_scraped (create stub row if missing)
    monitored = (
        db.query(MonitoredCompany)
        .filter(MonitoredCompany.ats_type == ats_type, MonitoredCompany.slug == slug)
        .first()
    )
    if not monitored:
        monitored = MonitoredCompany(
            name=slug.replace("-", " ").title(),
            slug=slug,
            ats_type=ats_type,
            career_url="",
            priority="cold",
            is_active=True,
        )
        db.add(monitored)
    monitored.last_scraped_at = datetime.utcnow()
    monitored.last_job_count = len(payload.jobs)
    monitored.is_active = True

    db.commit()
    return {
        "status": "ok",
        "ats_type": ats_type,
        "company_slug": slug,
        "received": len(payload.jobs),
        "created": created,
        "updated": updated,
    }
