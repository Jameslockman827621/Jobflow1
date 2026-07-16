"""Apply engine API: packages, captcha, headless apply, messaging bots."""

import json
from collections import Counter
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_admin, get_current_user
from app.database import get_db
from app.models.application import Application
from app.models.company import ApplyRun
from app.models.job import Job
from app.models.user import User
from app.services.apply_engine import answer_open_ended, build_apply_package, build_applicant_payload
from app.services.captcha import captcha_service
from app.services.headless_apply import run_headless_apply
from app.services.messaging import messaging_service
from app.services.apply_limits import check_apply_quota
from app.services.answer_bank import upsert_answer
from app.models.cv import CV
from app.models.profile import UserProfile
from app.tasks.headless_apply_tasks import apply_batch, apply_one

router = APIRouter()


class OpenEndedRequest(BaseModel):
    question: str
    job_id: Optional[int] = None
    answer: Optional[str] = None  # when set, upsert into answer bank
    save: bool = True


class CaptchaSolveRequest(BaseModel):
    captcha_type: str = "recaptcha_v2"
    site_key: str
    page_url: str


class HeadlessApplyRequest(BaseModel):
    application_id: int
    auto_submit: bool = False
    dry_run: bool = False
    async_queue: bool = False


class HeadlessBatchRequest(BaseModel):
    application_ids: List[int] = Field(default_factory=list)
    auto_submit: bool = False
    dry_run: bool = True
    max_per_batch: int = 50


class MessagingSendRequest(BaseModel):
    channel: str  # whatsapp | imessage
    to: str
    body: str


class MessagingInboundRequest(BaseModel):
    channel: str
    from_number: str
    body: str


class ApplyReportRequest(BaseModel):
    application_id: int
    fields_filled: int = 0
    steps_completed: int = 0
    status: str = "filled"
    ats: Optional[str] = None
    error: Optional[str] = None


class AutoApplySettingsUpdate(BaseModel):
    auto_apply_submit: Optional[bool] = None
    monitor_auto_queue: Optional[bool] = None


class HeadlessRetryRequest(BaseModel):
    application_ids: Optional[List[int]] = None
    statuses: List[str] = Field(default_factory=lambda: ["failed", "needs_user"])
    auto_submit: bool = True
    limit: int = 20


@router.get("/settings")
async def get_auto_apply_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """User opt-in status for genuine (submit) auto-apply."""
    from app.core.config import settings
    from app.services.ats_adapters.form_helpers import profile_completeness
    from app.services.apply_engine import build_applicant_payload
    from app.services.resume_files import ensure_resume_local_path

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    cv = (
        db.query(CV)
        .filter(CV.user_id == current_user.id)
        .order_by(CV.is_primary.desc(), CV.created_at.desc())
        .first()
    )
    payload = build_applicant_payload(current_user, profile, cv)
    if cv or payload.get("email"):
        try:
            ensure_resume_local_path(current_user.id, payload, cv)
        except Exception:
            pass
    completeness = profile_completeness(payload)
    opted_in = bool(getattr(current_user, "auto_apply_submit", False))
    monitor_q = bool(getattr(current_user, "monitor_auto_queue", False))

    return {
        "auto_apply_submit": opted_in,
        "monitor_auto_queue": monitor_q,
        "platform_allows_submit": bool(getattr(settings, "HEADLESS_APPLY_AUTO_SUBMIT", True)),
        "headless_enabled": bool(getattr(settings, "HEADLESS_APPLY_ENABLED", True)),
        "captcha_available": captcha_service.available,
        "profile_completeness": completeness,
        "genuine_ready": bool(
            opted_in
            and getattr(settings, "HEADLESS_APPLY_AUTO_SUBMIT", True)
            and not [m for m in completeness.get("missing", []) if m in ("first_name", "last_name", "email", "resume")]
        ),
        "message": (
            "Genuine auto-apply is ON — JobScale will submit applications for you."
            if opted_in
            else "Enable auto_apply_submit to let JobScale submit forms on your behalf."
        ),
    }


@router.patch("/settings")
async def update_auto_apply_settings(
    body: AutoApplySettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Opt in/out of genuine submit auto-apply and monitored-job auto-queue."""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.auto_apply_submit is not None:
        user.auto_apply_submit = bool(body.auto_apply_submit)
    if body.monitor_auto_queue is not None:
        user.monitor_auto_queue = bool(body.monitor_auto_queue)
    db.commit()
    db.refresh(user)
    return {
        "ok": True,
        "auto_apply_submit": bool(user.auto_apply_submit),
        "monitor_auto_queue": bool(user.monitor_auto_queue),
        "message": (
            "Settings updated."
        ),
    }


@router.get("/package/{job_id}")
async def get_apply_package(
    job_id: int,
    application_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    application = None
    if application_id:
        application = (
            db.query(Application)
            .filter(Application.id == application_id, Application.user_id == current_user.id)
            .first()
        )
    return build_apply_package(db, current_user, job, application)


@router.get("/package/application/{application_id}")
async def get_package_for_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = (
        db.query(Application)
        .filter(Application.id == application_id, Application.user_id == current_user.id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    job = db.query(Job).filter(Job.id == application.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return build_apply_package(db, current_user, job, application)


@router.post("/answer")
async def answer_question(
    body: OpenEndedRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    cv = (
        db.query(CV)
        .filter(CV.user_id == current_user.id)
        .order_by(CV.is_primary.desc(), CV.created_at.desc())
        .first()
    )
    payload = build_applicant_payload(current_user, profile, cv)
    job = db.query(Job).filter(Job.id == body.job_id).first() if body.job_id else None

    # Explicit save of a user-provided answer
    if body.answer and body.save:
        row = upsert_answer(db, current_user.id, body.question, body.answer)
        return {
            "question": body.question,
            "answer": row.answer,
            "saved": True,
            "source": "user",
            "use_count": row.use_count,
        }

    answer = await answer_open_ended(
        body.question, payload, job, db=db, user_id=current_user.id
    )
    if body.save and answer:
        try:
            upsert_answer(db, current_user.id, body.question, answer)
        except Exception:
            pass
    return {"question": body.question, "answer": answer, "saved": bool(body.save and answer)}


@router.post("/captcha/solve")
async def solve_captcha(
    body: CaptchaSolveRequest,
    current_user: User = Depends(get_current_user),
):
    result = await captcha_service.solve(body.captcha_type, body.site_key, body.page_url)
    return result


@router.get("/captcha/status")
async def captcha_status(current_user: User = Depends(get_current_user)):
    return {
        "available": captcha_service.available,
        "provider": "mock" if captcha_service.mock_mode else "2captcha",
        "mock": captcha_service.mock_mode,
    }


@router.post("/headless")
async def headless_apply(
    body: HeadlessApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not body.dry_run:
        quota = check_apply_quota(db, current_user.id, requested=1, user=current_user)
        if not quota["allowed"]:
            raise HTTPException(status_code=429, detail=quota)
    if body.async_queue:
        task = apply_one.delay(
            current_user.id,
            body.application_id,
            auto_submit=body.auto_submit,
            dry_run=body.dry_run,
        )
        return {"ok": True, "queued": True, "task_id": task.id}
    return await run_headless_apply(
        db,
        current_user,
        body.application_id,
        auto_submit=body.auto_submit,
        dry_run=body.dry_run,
    )


@router.post("/headless/batch")
async def headless_batch(
    body: HeadlessBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not body.application_ids:
        raise HTTPException(status_code=400, detail="No application_ids")
    if len(body.application_ids) > 200:
        raise HTTPException(status_code=400, detail="Max 200 applications per batch")
    max_per = min(body.max_per_batch, 100)
    requested = len(body.application_ids)
    to_queue = body.application_ids[:max_per]
    if not body.dry_run:
        quota = check_apply_quota(db, current_user.id, requested=len(to_queue), user=current_user)
        if not quota["allowed"]:
            raise HTTPException(status_code=429, detail=quota)
    import uuid as _uuid

    batch_id = str(_uuid.uuid4())
    task = apply_batch.delay(
        current_user.id,
        body.application_ids,
        auto_submit=body.auto_submit,
        dry_run=body.dry_run,
        max_per_batch=max_per,
        batch_id=batch_id,
    )
    return {
        "ok": True,
        "queued": True,
        "batch_id": batch_id,
        "task_id": task.id,
        "requested": requested,
        "queued_count": len(to_queue),
        "deferred_count": max(0, requested - len(to_queue)),
        "fan_out": True,
        "message": (
            f"Batch headless apply queued: {len(to_queue)}/{requested} "
            f"(batch {batch_id})"
        ),
    }


@router.get("/headless/batch/{batch_id}")
async def headless_batch_status(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregate ApplyRun outcomes for a batch_id (DB-backed, not Redis TTL)."""
    # Prefer SQL like-filter so high-volume users don't miss batches beyond "last 500"
    needle = f'%"{batch_id}"%'
    rows = (
        db.query(ApplyRun)
        .filter(
            ApplyRun.user_id == current_user.id,
            ApplyRun.meta_json.isnot(None),
            ApplyRun.meta_json.like(needle),
        )
        .order_by(ApplyRun.created_at.desc())
        .limit(300)
        .all()
    )
    matched = []
    metas = []
    for r in rows:
        try:
            meta = json.loads(r.meta_json or "{}")
        except Exception:
            meta = {}
        if meta.get("batch_id") == batch_id:
            matched.append(r)
            metas.append(meta)
    by_status = Counter(r.status for r in matched)
    needs_reconnect = sum(
        1
        for m in metas
        if m.get("blocked_reason") == "login_required"
        or m.get("session_invalidated")
        or m.get("connect_hint")
    )
    return {
        "batch_id": batch_id,
        "total": len(matched),
        "by_status": dict(by_status),
        "submitted": by_status.get("submitted", 0),
        "failed": by_status.get("failed", 0) + by_status.get("stale", 0),
        "needs_user": by_status.get("needs_user", 0),
        "running": by_status.get("running", 0) + by_status.get("queued", 0),
        "needs_reconnect": needs_reconnect,
        "done": sum(
            by_status.get(s, 0)
            for s in (
                "submitted",
                "filled",
                "failed",
                "stale",
                "needs_user",
                "deferred",
                "skipped",
            )
        ),
        "runs": [
            {
                "id": r.id,
                "application_id": r.application_id,
                "status": r.status,
                "ats_type": r.ats_type,
                "fields_filled": r.fields_filled,
                "error": r.error,
                # Dashboard reconnect UX depends on meta (blocked_reason / connect_hint)
                "meta": {
                    "blocked_reason": metas[i].get("blocked_reason"),
                    "connect_hint": metas[i].get("connect_hint"),
                    "session_invalidated": metas[i].get("session_invalidated"),
                    "submit_uncertain": metas[i].get("submit_uncertain"),
                    "already_applied": metas[i].get("already_applied"),
                    "session_used": metas[i].get("session_used"),
                },
            }
            for i, r in enumerate(matched[:100])
        ],
    }


@router.get("/metrics/apply")
async def apply_metrics(
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Last-N-hours apply success rates for the current user (scale observability)."""
    since = datetime.utcnow() - timedelta(hours=min(max(hours, 1), 168))
    rows = (
        db.query(ApplyRun)
        .filter(ApplyRun.user_id == current_user.id, ApplyRun.created_at >= since)
        .all()
    )
    by_status = Counter(r.status for r in rows)
    by_ats = Counter((r.ats_type or "unknown") for r in rows)
    submitted = by_status.get("submitted", 0)
    attempted = len([r for r in rows if r.status not in ("deferred", "skipped")])
    return {
        "window_hours": min(max(hours, 1), 168),
        "total_runs": len(rows),
        "attempted": attempted,
        "submitted": submitted,
        "success_rate": round(submitted / attempted, 3) if attempted else 0.0,
        "by_status": dict(by_status),
        "by_ats": dict(by_ats),
        "needs_user": by_status.get("needs_user", 0),
        "failed": by_status.get("failed", 0),
        "stale": by_status.get("stale", 0),
    }


@router.get("/metrics/ops")
async def apply_ops_metrics(
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Admin: global ApplyRun health (stale/failed/submitted) across all users."""
    _ = current_user
    since = datetime.utcnow() - timedelta(hours=min(max(hours, 1), 168))
    rows = db.query(ApplyRun).filter(ApplyRun.created_at >= since).all()
    by_status = Counter(r.status for r in rows)
    by_ats = Counter((r.ats_type or "unknown") for r in rows)
    return {
        "window_hours": min(max(hours, 1), 168),
        "total_runs": len(rows),
        "by_status": dict(by_status),
        "by_ats": dict(by_ats),
        "stale": by_status.get("stale", 0),
        "failed": by_status.get("failed", 0),
        "needs_user": by_status.get("needs_user", 0),
        "submitted": by_status.get("submitted", 0),
        "running": by_status.get("running", 0),
        "queued": by_status.get("queued", 0),
    }


@router.post("/headless/retry")
async def headless_retry(
    body: HeadlessRetryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-queue failed / needs_user apply runs for genuine retry."""
    statuses = body.statuses or ["failed", "needs_user"]
    q = (
        db.query(ApplyRun)
        .filter(ApplyRun.user_id == current_user.id, ApplyRun.status.in_(statuses))
        .order_by(ApplyRun.created_at.desc())
    )
    if body.application_ids:
        q = q.filter(ApplyRun.application_id.in_(body.application_ids))
    rows = q.limit(min(body.limit, 50)).all()
    # Deduplicate by application_id (latest run wins)
    seen = set()
    app_ids = []
    for r in rows:
        if r.application_id in seen:
            continue
        seen.add(r.application_id)
        app_ids.append(r.application_id)
    if not app_ids:
        return {"ok": True, "queued": 0, "application_ids": [], "message": "Nothing to retry"}

    if body.auto_submit:
        quota = check_apply_quota(db, current_user.id, requested=len(app_ids), user=current_user)
        if not quota["allowed"]:
            raise HTTPException(status_code=429, detail=quota)

    task = apply_batch.delay(
        current_user.id,
        app_ids,
        auto_submit=body.auto_submit,
        dry_run=False,
        max_per_batch=min(len(app_ids), 50),
    )
    return {
        "ok": True,
        "queued": len(app_ids),
        "application_ids": app_ids,
        "task_id": task.id,
        "auto_submit": body.auto_submit,
    }


@router.get("/quota")
async def apply_quota(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return check_apply_quota(db, current_user.id, requested=0, user=current_user)


@router.get("/runs")
async def list_apply_runs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(ApplyRun)
        .filter(ApplyRun.user_id == current_user.id)
        .order_by(ApplyRun.created_at.desc())
        .limit(min(limit, 200))
        .all()
    )
    return {
        "runs": [
            {
                "id": r.id,
                "application_id": r.application_id,
                "job_id": r.job_id,
                "mode": r.mode,
                "ats_type": r.ats_type,
                "status": r.status,
                "steps_completed": r.steps_completed,
                "fields_filled": r.fields_filled,
                "captcha_solved": r.captcha_solved,
                "error": r.error,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            }
            for r in rows
        ],
        "total": len(rows),
    }


@router.post("/report")
async def report_extension_apply(
    body: ApplyReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Extension reports a fill attempt → create ApplyRun(mode=extension)."""
    application = (
        db.query(Application)
        .filter(Application.id == body.application_id, Application.user_id == current_user.id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    now = datetime.utcnow()
    run = ApplyRun(
        user_id=current_user.id,
        application_id=application.id,
        job_id=application.job_id,
        mode="extension",
        ats_type=body.ats,
        status=body.status or "filled",
        steps_completed=body.steps_completed or 0,
        fields_filled=body.fields_filled or 0,
        error=(body.error[:2000] if body.error else None),
        started_at=now,
        finished_at=now,
    )
    db.add(run)
    if body.status == "submitted":
        application.status = "submitted"
        application.stage = "applied"
        application.submitted_at = application.submitted_at or now
        application.applied_via = "extension"
    elif body.status in ("filled", "needs_user", "captcha"):
        if application.status in ("draft", "ready_to_apply"):
            application.status = "in_progress"
        application.applied_via = application.applied_via or "extension"
    db.commit()
    db.refresh(run)
    return {
        "ok": True,
        "apply_run_id": run.id,
        "mode": "extension",
        "status": run.status,
        "fields_filled": run.fields_filled,
        "steps_completed": run.steps_completed,
    }


class BoardSessionUpsert(BaseModel):
    storage_state: dict
    label: Optional[str] = None


class BoardCookiesUpsert(BaseModel):
    cookies: List[dict]
    label: Optional[str] = None


@router.get("/connect/status")
async def connect_status_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Whether LinkedIn / Indeed are connected for Easy Apply."""
    from app.services.board_session import connect_status

    return connect_status(db, current_user.id)


@router.post("/board-sessions/{board}/from-cookies")
async def session_from_cookies(
    board: str,
    body: BoardCookiesUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Extension Connect path: Chrome cookies → Playwright storage_state → BoardSession.
    This is how users 'connect LinkedIn/Indeed' for genuine Easy Apply.
    """
    from app.services.board_session import cookies_to_storage_state, upsert_board_session

    try:
        state = cookies_to_storage_state(body.cookies, board)
        row = upsert_board_session(
            db,
            current_user.id,
            board,
            state,
            label=body.label or f"extension-{board}",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    cookie_count = len((state or {}).get("cookies") or [])
    return {
        "ok": True,
        "connected": True,
        "board": row.board,
        "cookie_count": cookie_count,
        "message": f"{board} connected. Easy Apply can run with your session.",
    }


@router.get("/board-sessions")
async def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List LinkedIn/Indeed login sessions for headless Easy Apply."""
    from app.services.board_session import list_board_sessions

    return {"sessions": list_board_sessions(db, current_user.id)}


@router.get("/board-sessions/{board}")
async def get_session(
    board: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.board_session import get_board_session

    row = get_board_session(db, current_user.id, board)
    if not row:
        raise HTTPException(status_code=404, detail="No session for board")
    return {
        "board": row.board,
        "label": row.label,
        "is_valid": bool(row.is_valid),
        "has_storage_state": True,
        "last_used_at": row.last_used_at.isoformat() if row.last_used_at else None,
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
    }


@router.put("/board-sessions/{board}")
async def put_session(
    board: str,
    body: BoardSessionUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload Playwright storage_state JSON for LinkedIn or Indeed.
    Export via: await context.storage_state() in a logged-in browser.
    """
    from app.services.board_session import upsert_board_session

    try:
        row = upsert_board_session(
            db,
            current_user.id,
            board,
            body.storage_state,
            label=body.label,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "ok": True,
        "board": row.board,
        "label": row.label,
        "message": f"{row.board} session saved — headless Easy Apply can use it.",
    }


@router.delete("/board-sessions/{board}")
async def delete_session(
    board: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.board_session import delete_board_session

    ok = delete_board_session(db, current_user.id, board)
    if not ok:
        raise HTTPException(status_code=404, detail="No session for board")
    return {"ok": True, "deleted": board}


@router.get("/board-classify")
async def board_classify_endpoint(
    url: str,
    current_user: User = Depends(get_current_user),
):
    """Preview how a job URL will be routed (Easy Apply / handoff / ATS)."""
    from app.services.board_classify import classify_url

    return classify_url(url)


@router.get("/messaging/status")
async def messaging_status(current_user: User = Depends(get_current_user)):
    return messaging_service.status()


@router.post("/messaging/send")
async def messaging_send(
    body: MessagingSendRequest,
    current_user: User = Depends(get_current_user),
):
    return await messaging_service.send(body.channel, body.to, body.body)


@router.post("/messaging/inbound")
async def messaging_inbound(
    body: MessagingInboundRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    apps = db.query(Application).filter(Application.user_id == current_user.id).all()
    ready = [a for a in apps if a.status == "ready_to_apply"]
    jobs = []
    for a in ready[:10]:
        job = db.query(Job).filter(Job.id == a.job_id).first()
        if job:
            jobs.append({"id": job.id, "title": job.title, "company": job.company})
    ctx = {
        "email": current_user.email,
        "submitted": len([a for a in apps if a.status == "submitted"]),
        "ready": len(ready),
        "interviews": len([a for a in apps if a.stage in ("phone_screen", "technical", "onsite")]),
        "jobs": jobs,
    }
    return await messaging_service.handle_inbound(
        body.channel,
        body.from_number,
        body.body,
        ctx,
        db=db,
        user_id=current_user.id,
    )


@router.post("/messaging/twilio")
async def messaging_twilio_webhook(
    request: Request,
    db: Session = Depends(get_db),
    Body: Optional[str] = Form(None),
    From: Optional[str] = Form(None),
):
    """
    Twilio WhatsApp/SMS webhook (no auth).
    form-urlencoded Body / From → look up user by CV.phone digits.
    """
    # Also accept raw form if Form() binding missed
    if Body is None or From is None:
        try:
            form = await request.form()
            Body = Body or form.get("Body")
            From = From or form.get("From")
        except Exception:
            pass

    from_number = From or ""
    body_text = Body or ""

    user = messaging_service.lookup_user_by_phone(db, from_number)
    if not user:
        help_msg = (
            "JobScale: phone not linked. Add your phone on your CV, then text HELP.\n"
            "Commands: APPLY <job_id>, STATUS, JOBS, HELP"
        )
        # Twilio expects TwiML or empty 200; return plain help body for visibility
        return Response(
            content=(
                '<?xml version="1.0" encoding="UTF-8"?>'
                f"<Response><Message>{help_msg}</Message></Response>"
            ),
            media_type="application/xml",
        )

    apps = db.query(Application).filter(Application.user_id == user.id).all()
    ready = [a for a in apps if a.status == "ready_to_apply"]
    jobs = []
    for a in ready[:10]:
        job = db.query(Job).filter(Job.id == a.job_id).first()
        if job:
            jobs.append({"id": job.id, "title": job.title, "company": job.company})
    ctx = {
        "email": user.email,
        "submitted": len([a for a in apps if a.status == "submitted"]),
        "ready": len(ready),
        "interviews": len([a for a in apps if a.stage in ("phone_screen", "technical", "onsite")]),
        "jobs": jobs,
    }

    # Prefer WhatsApp channel when From is whatsapp:
    channel = "whatsapp" if str(from_number).startswith("whatsapp:") else "whatsapp"
    result = await messaging_service.handle_inbound(
        channel,
        from_number,
        body_text,
        ctx,
        db=db,
        user_id=user.id,
    )
    reply = result.get("reply") or "OK"
    # Escape minimal XML
    safe = (
        reply.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return Response(
        content=(
            '<?xml version="1.0" encoding="UTF-8"?>'
            f"<Response><Message>{safe}</Message></Response>"
        ),
        media_type="application/xml",
    )
