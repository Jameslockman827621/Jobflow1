"""Queue high-match monitored jobs for opted-in users (no mock — real DB writes)."""

from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.auto_apply import UserAutoApplyJob
from app.models.job import Job
from app.models.preferences import UserPreferences
from app.models.profile import UserProfile
from app.models.user import User
from app.services.matching import JobMatcher

logger = logging.getLogger(__name__)

DEFAULT_MIN_SCORE = 70.0
MAX_QUEUE_PER_EVENT = 10


def _company_matches_prefs(company_name: str, prefs: Optional[UserPreferences]) -> bool:
    if not prefs or not prefs.is_active:
        return False
    targets = [c.lower() for c in (prefs.target_companies or []) if c]
    excludes = [c.lower() for c in (prefs.exclude_companies or []) if c]
    name = (company_name or "").lower()
    if excludes and any(x in name or name in x for x in excludes):
        return False
    if not targets:
        # Opt-in users with no company filter still get scored matches
        return True
    return any(t in name or name in t for t in targets)


def auto_queue_new_jobs_for_opted_in_users(
    db: Session,
    *,
    company_name: str,
    job_ids: List[int],
    min_score: float = DEFAULT_MIN_SCORE,
) -> dict:
    """
    For users with ``monitor_auto_queue`` enabled, add high-match new jobs
    to their auto-apply list (extension / headless queue source of truth).
    """
    if not job_ids:
        return {"queued": 0, "users": 0}

    jobs = db.query(Job).filter(Job.id.in_(job_ids), Job.is_active == True).all()  # noqa: E712
    if not jobs:
        return {"queued": 0, "users": 0}

    users = (
        db.query(User)
        .filter(User.is_active == True, User.monitor_auto_queue == True)  # noqa: E712
        .all()
    )
    matcher = JobMatcher(db)
    queued = 0
    touched_users = 0

    for user in users:
        prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
        if not _company_matches_prefs(company_name, prefs):
            continue
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if not profile:
            continue

        user_queued = 0
        for job in jobs:
            if user_queued >= MAX_QUEUE_PER_EVENT:
                break
            try:
                score = matcher.calculate_match_score(profile, job)
            except Exception:
                continue
            if score < min_score:
                continue
            exists = (
                db.query(UserAutoApplyJob)
                .filter(UserAutoApplyJob.user_id == user.id, UserAutoApplyJob.job_id == job.id)
                .first()
            )
            if exists:
                continue
            db.add(UserAutoApplyJob(user_id=user.id, job_id=job.id))
            if job.match_score is None or score > (job.match_score or 0):
                job.match_score = score
            user_queued += 1
            queued += 1
        if user_queued:
            touched_users += 1

    if queued:
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("auto_queue commit failed: %s", exc)
            return {"queued": 0, "users": 0, "error": str(exc)[:200]}

    return {"queued": queued, "users": touched_users, "min_score": min_score}
