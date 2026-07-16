"""Celery tasks for unattended / scaled headless apply."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from app.database import SessionLocal
from app.models.company import ApplyRun
from app.models.user import User
from app.services.apply_limits import check_apply_quota, chunk_ids
from app.services.headless_apply import run_headless_apply
from app.tasks import celery_app


def _run_async(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)


@celery_app.task(
    bind=True,
    name="app.tasks.headless_apply_tasks.apply_one",
    soft_time_limit=240,
    time_limit=300,
    acks_late=True,
    reject_on_worker_lost=True,
    autoretry_for=(TimeoutError,),
    retry_backoff=True,
    retry_backoff_max=60,
    max_retries=2,
    rate_limit="20/m",
)
def apply_one(
    self,
    user_id: int,
    application_id: int,
    auto_submit: bool = False,
    dry_run: bool = False,
    batch_id: Optional[str] = None,
):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"ok": False, "error": "user_not_found"}

        if not dry_run:
            quota = check_apply_quota(db, user_id, requested=1)
            if not quota["allowed"]:
                run = ApplyRun(
                    user_id=user_id,
                    application_id=application_id,
                    mode="headless",
                    status="deferred",
                    error=quota.get("reason") or "quota_exceeded",
                    started_at=datetime.utcnow(),
                    finished_at=datetime.utcnow(),
                    meta_json=json.dumps({"batch_id": batch_id, "quota": quota}),
                )
                db.add(run)
                db.commit()
                return {
                    "ok": False,
                    "error": "quota_exceeded",
                    "quota": quota,
                    "deferred": True,
                    "batch_id": batch_id,
                }

        return _run_async(
            run_headless_apply(
                db,
                user,
                application_id,
                auto_submit=auto_submit,
                dry_run=dry_run,
                batch_id=batch_id,
            )
        )
    finally:
        db.close()


@celery_app.task(name="app.tasks.headless_apply_tasks.apply_batch")
def apply_batch(
    user_id: int,
    application_ids: List[int],
    auto_submit: bool = False,
    dry_run: bool = True,
    max_per_batch: int = 50,
):
    """
    Scale path: fan out one Celery task per application onto the apply queue.
    Returns batch_id for DB-backed progress aggregation.
    """
    ids = list(application_ids or [])
    requested = len(ids)
    capped = ids[:max_per_batch]
    deferred_ids = ids[max_per_batch:]
    batch_id = str(uuid.uuid4())
    task_ids = []
    for app_id in capped:
        async_result = apply_one.apply_async(
            args=(user_id, app_id),
            kwargs={
                "auto_submit": auto_submit,
                "dry_run": dry_run,
                "batch_id": batch_id,
            },
            queue="apply",
        )
        task_ids.append({"application_id": app_id, "task_id": async_result.id})

    return {
        "ok": True,
        "batch_id": batch_id,
        "total": len(task_ids),
        "requested": requested,
        "queued_count": len(task_ids),
        "deferred_count": len(deferred_ids),
        "deferred_ids": deferred_ids[:50],
        "fan_out": True,
        "tasks": task_ids,
        "message": f"Queued {len(task_ids)}/{requested} headless apply tasks (batch {batch_id})",
    }


@celery_app.task(name="app.tasks.headless_apply_tasks.fail_stale_apply_runs")
def fail_stale_apply_runs(max_age_minutes: int = 15):
    """Mark ApplyRuns stuck in running as failed/stale so quota + dashboards stay honest."""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        rows = (
            db.query(ApplyRun)
            .filter(ApplyRun.status == "running", ApplyRun.started_at < cutoff)
            .all()
        )
        for r in rows:
            r.status = "stale"
            r.error = (r.error or "") + ";stale_timeout" if r.error else "stale_timeout"
            r.finished_at = datetime.utcnow()
            try:
                meta = json.loads(r.meta_json or "{}")
            except Exception:
                meta = {}
            meta["stale"] = True
            meta["stale_after_minutes"] = max_age_minutes
            r.meta_json = json.dumps(meta)
        db.commit()
        return {"ok": True, "marked_stale": len(rows)}
    finally:
        db.close()
