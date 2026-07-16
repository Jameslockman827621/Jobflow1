"""Per-user apply rate limits for scale without spam/ban risk."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict

from sqlalchemy.orm import Session

from app.models.company import ApplyRun


# Soft product limits (can be raised by plan later)
DEFAULT_DAILY_LIMIT = 100
DEFAULT_HOURLY_LIMIT = 30
DEFAULT_BATCH_LIMIT = 50


def check_apply_quota(db: Session, user_id: int, requested: int = 1) -> Dict:
    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)

    hourly = (
        db.query(ApplyRun)
        .filter(ApplyRun.user_id == user_id, ApplyRun.created_at >= hour_ago)
        .count()
    )
    daily = (
        db.query(ApplyRun)
        .filter(ApplyRun.user_id == user_id, ApplyRun.created_at >= day_ago)
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
        "hourly_limit": DEFAULT_HOURLY_LIMIT,
        "daily_limit": DEFAULT_DAILY_LIMIT,
        "batch_limit": DEFAULT_BATCH_LIMIT,
        "remaining_today": max(DEFAULT_DAILY_LIMIT - daily, 0),
    }
