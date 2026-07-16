"""Monitored company / career-page directory for scaled ATS coverage."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Index, Text
from datetime import datetime

from app.models.base import Base, TimestampMixin


class MonitoredCompany(Base, TimestampMixin):
    """A career page / ATS board we continuously monitor for new jobs."""

    __tablename__ = "monitored_companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(200), nullable=False, index=True)  # ATS subdomain / board token
    ats_type = Column(String(50), nullable=False, index=True)  # greenhouse, lever, workable, ashby, custom
    career_url = Column(String(500))
    industry = Column(String(100))
    country = Column(String(10), default="US")
    # hot = near-real-time, warm = frequent, cold = baseline
    priority = Column(String(20), default="cold", index=True)
    is_active = Column(Boolean, default=True, index=True)
    last_scraped_at = Column(DateTime, nullable=True)
    last_job_count = Column(Integer, default=0)
    last_fingerprint = Column(String(64), nullable=True)  # hash of external_ids from last scrape
    scrape_failures = Column(Integer, default=0)
    avg_scrape_ms = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("uix_monitored_ats_slug", "ats_type", "slug", unique=True),
        Index("idx_monitored_priority_active", "priority", "is_active"),
    )


class ApplyRun(Base, TimestampMixin):
    """Server-side / extension apply attempt telemetry for scale & debugging."""

    __tablename__ = "apply_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    application_id = Column(Integer, nullable=True, index=True)
    job_id = Column(Integer, nullable=True, index=True)
    mode = Column(String(40), nullable=False)  # extension, headless, messaging
    ats_type = Column(String(50))
    status = Column(String(40), default="queued")  # queued, running, filled, submitted, failed, captcha, needs_user
    steps_completed = Column(Integer, default=0)
    fields_filled = Column(Integer, default=0)
    captcha_solved = Column(Boolean, default=False)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    meta_json = Column(Text, nullable=True)  # JSON string for extras
