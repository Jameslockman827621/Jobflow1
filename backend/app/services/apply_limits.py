"""Per-user apply rate limits for scale without spam/ban risk."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Iterable

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.company import ApplyRun


# Soft product limits (can be raised by plan later)
DEFAULT_DAILY_LIMIT = 100
DEFAULT_HOURLY_LIMIT = 30
DEFAULT_BATCH_LIMIT = 50

# Only these count toward quota (failed/dry_run/stale do not burn capacity)
BILLABLE_STATUSES = ("submitted", "filled", "running", "queued", "needs_user")
NON_BILLABLE_STATUSES = ("failed", "stale", "deferred", "skipped")


def _billable_filter(query):
    """Live headless/extension attempts that consume capacity."""
    return query.filter(
        ApplyRun.status.in_(BILLABLE_STATUSES),
        # dry_run runs store dry_run in meta — exclude when tagged
        or_(ApplyRun.meta_json.is_(None), ~ApplyRun.meta_json.like('%"dry_run": true%')),
        or_(ApplyRun.meta_json.is_(None), ~ApplyRun.meta_json.like('%"dry_run":true%')),
    )


def check_apply_quota(db: Session, user_id: int, requested: int = 1) -> Dict:
    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)

    hourly = _billable_filter(
        db.query(ApplyRun).filter(ApplyRun.user_id == user_id, ApplyRun.created_at >= hour_ago)
    ).count()
    daily = _billable_filter(
        db.query(ApplyRun).filter(ApplyRun.user_id == user_id, ApplyRun.created_at >= day_ago)
    ).count()

    # Successful submits tracked separately for dashboards
    submitted_today = (
        db.query(ApplyRun)
        .filter(
            ApplyRun.user_id == user_id,
            ApplyRun.created_at >= day_ago,
            ApplyRun.status == "submitted",
        )
        .count()
    )

    allowed = True
    reason = None
    if hourly + requested > DEFAULT_HOURLY_LIMIT:
        allowed = False
        reason = f"hourly_limit_{DEFAULT_HOURLY_LIMIT}"
    elif daily + requested > DEFAULT_DAILY_LIMIT:
        allowed = False
        reason = f"daily_limit_{DEFAULT_DAILY_LIMIT}"
    elif requested > DEFAULT_BATCH_LIMIT:
        allowed = False
        reason = f"batch_limit_{DEFAULT_BATCH_LIMIT}"

    return {
        "allowed": allowed,
        "reason": reason,
        "hourly_used": hourly,
        "daily_used": daily,
        "submitted_today": submitted_today,
        "hourly_limit": DEFAULT_HOURLY_LIMIT,
        "daily_limit": DEFAULT_DAILY_LIMIT,
        "batch_limit": DEFAULT_BATCH_LIMIT,
        "remaining_today": max(DEFAULT_DAILY_LIMIT - daily, 0),
        "billable_statuses": list(BILLABLE_STATUSES),
    }


def chunk_ids(ids: Iterable[int], size: int) -> list:
    items = list(ids or [])
    size = max(1, int(size))
    return [items[i : i + size] for i in range(0, len(items), size)]
