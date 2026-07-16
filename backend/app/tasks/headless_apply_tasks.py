"""Celery tasks for unattended / scaled headless apply."""

from __future__ import annotations

import asyncio
from typing import List

from app.database import SessionLocal
from app.models.user import User
from app.services.headless_apply import run_headless_apply
from app.tasks import celery_app


def _run_async(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)


@celery_app.task(
    name="app.tasks.headless_apply_tasks.apply_one",
    soft_time_limit=240,
    time_limit=300,
    acks_late=True,
)
def apply_one(user_id: int, application_id: int, auto_submit: bool = False, dry_run: bool = False):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"ok": False, "error": "user_not_found"}
        return _run_async(
            run_headless_apply(
                db,
                user,
                application_id,
                auto_submit=auto_submit,
                dry_run=dry_run,
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
    Scale path: fan out one Celery task per application (not sequential in-process).
    Avoids the 5-minute batch time-limit killing mid-queue runs.
    """
    ids = list(application_ids or [])[:max_per_batch]
    task_ids = []
    for app_id in ids:
        async_result = apply_one.delay(
            user_id, app_id, auto_submit=auto_submit, dry_run=dry_run
        )
        task_ids.append({"application_id": app_id, "task_id": async_result.id})
    return {
        "ok": True,
        "total": len(task_ids),
        "fan_out": True,
        "tasks": task_ids,
        "message": f"Queued {len(task_ids)} headless apply tasks",
    }
