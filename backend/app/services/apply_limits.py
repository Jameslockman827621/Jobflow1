"""Per-user apply rate limits — plan-aware, billable statuses only."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Iterable, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.company import ApplyRun
from app.models.user import User


# Plan limits — free must match billing marketing (5 apps/month)
PLAN_QUOTAS: Dict[str, Dict[str, int]] = {
    "free": {"hourly": 5, "daily": 5, "batch": 5, "monthly": 5},
    "pro": {"hourly": 30, "daily": 100, "batch": 50, "monthly": 500},
    "premium": {"hourly": 50, "daily": 200, "batch": 100, "monthly": 2000},
}

# Soft defaults if plan missing
DEFAULT_DAILY_LIMIT = PLAN_QUOTAS["free"]["daily"]
DEFAULT_HOURLY_LIMIT = PLAN_QUOTAS["free"]["hourly"]
DEFAULT_BATCH_LIMIT = PLAN_QUOTAS["free"]["batch"]

BILLABLE_STATUSES = ("submitted", "filled", "running", "queued", "needs_user")
NON_BILLABLE_STATUSES = ("failed", "stale", "deferred", "skipped")

# Connect / profile gates must NOT burn free-tier quota
_NON_BILLABLE_META_LIKE = (
    '%"blocked_reason": "login_required"%',
    '%"blocked_reason":"login_required"%',
    "%profile_incomplete%",
    '%"blocked_reason": "workday_account_wall"%',
    '%"blocked_reason":"workday_account_wall"%',
)


def normalize_plan(plan: Optional[str]) -> str:
    p = (plan or "free").lower().strip().split("_")[0]
    return p if p in PLAN_QUOTAS else "free"


def limits_for_plan(plan: Optional[str]) -> Dict[str, int]:
    return dict(PLAN_QUOTAS[normalize_plan(plan)])


def _billable_filter(query):
    """Live headless/extension attempts that consume capacity.

    Excludes dry_run rows and connect/profile soft-blocks so users are not
    punished when LinkedIn/Indeed session is missing or profile is incomplete.
    """
    q = query.filter(
        ApplyRun.status.in_(BILLABLE_STATUSES),
        or_(ApplyRun.meta_json.is_(None), ~ApplyRun.meta_json.like('%"dry_run": true%')),
        or_(ApplyRun.meta_json.is_(None), ~ApplyRun.meta_json.like('%"dry_run":true%')),
    )
    for marker in _NON_BILLABLE_META_LIKE:
        q = q.filter(or_(ApplyRun.meta_json.is_(None), ~ApplyRun.meta_json.like(marker)))
    return q


def check_apply_quota(
    db: Session,
    user_id: int,
    requested: int = 1,
    *,
    plan: Optional[str] = None,
    user: Optional[User] = None,
) -> Dict:
    if user is not None:
        plan = getattr(user, "subscription_plan", None) or plan
        user_id = user.id
    elif plan is None:
        row = db.query(User).filter(User.id == user_id).first()
        plan = getattr(row, "subscription_plan", None) if row else "free"

    limits = limits_for_plan(plan)
    hourly_limit = limits["hourly"]
    daily_limit = limits["daily"]
    batch_limit = limits["batch"]
    monthly_limit = limits["monthly"]

    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    hourly = _billable_filter(
        db.query(ApplyRun).filter(ApplyRun.user_id == user_id, ApplyRun.created_at >= hour_ago)
    ).count()
    daily = _billable_filter(
        db.query(ApplyRun).filter(ApplyRun.user_id == user_id, ApplyRun.created_at >= day_ago)
    ).count()
    monthly = _billable_filter(
        db.query(ApplyRun).filter(ApplyRun.user_id == user_id, ApplyRun.created_at >= month_start)
    ).count()

    submitted_today = (
        db.query(ApplyRun)
        .filter(
            ApplyRun.user_id == user_id,
            ApplyRun.created_at >= day_ago,
            ApplyRun.status == "submitted",
        )
        .count()
    )
    submitted_month = (
        db.query(ApplyRun)
        .filter(
            ApplyRun.user_id == user_id,
            ApplyRun.created_at >= month_start,
            ApplyRun.status == "submitted",
        )
        .count()
    )

    allowed = True
    reason = None
    if requested > batch_limit:
        allowed = False
        reason = f"batch_limit_{batch_limit}"
    elif hourly + requested > hourly_limit:
        allowed = False
        reason = f"hourly_limit_{hourly_limit}"
    elif daily + requested > daily_limit:
        allowed = False
        reason = f"daily_limit_{daily_limit}"
    elif monthly + requested > monthly_limit:
        allowed = False
        reason = f"monthly_limit_{monthly_limit}"

    return {
        "allowed": allowed,
        "reason": reason,
        "plan": normalize_plan(plan),
        "hourly_used": hourly,
        "daily_used": daily,
        "monthly_used": monthly,
        "submitted_today": submitted_today,
        "submitted_month": submitted_month,
        "hourly_limit": hourly_limit,
        "daily_limit": daily_limit,
        "batch_limit": batch_limit,
        "monthly_limit": monthly_limit,
        "remaining_today": max(daily_limit - daily, 0),
        "remaining_month": max(monthly_limit - monthly, 0),
        "billable_statuses": list(BILLABLE_STATUSES),
    }


def chunk_ids(ids: Iterable[int], size: int) -> list:
    items = list(ids or [])
    size = max(1, int(size))
    return [items[i : i + size] for i in range(0, len(items), size)]
