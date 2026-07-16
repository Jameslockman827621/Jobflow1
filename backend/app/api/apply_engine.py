"""Apply engine API: packages, captcha, headless apply, messaging bots."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
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
from app.models.cv import CV
from app.models.profile import UserProfile
from app.tasks.headless_apply_tasks import apply_batch, apply_one

router = APIRouter()


class OpenEndedRequest(BaseModel):
    question: str
    job_id: Optional[int] = None


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
    answer = await answer_open_ended(body.question, payload, job)
    return {"question": body.question, "answer": answer}


@router.post("/captcha/solve")
async def solve_captcha(
    body: CaptchaSolveRequest,
    current_user: User = Depends(get_current_user),
):
    result = await captcha_service.solve(body.captcha_type, body.site_key, body.page_url)
    return result


@router.get("/captcha/status")
async def captcha_status(current_user: User = Depends(get_current_user)):
    return {"available": captcha_service.available, "provider": "2captcha"}


@router.post("/headless")
async def headless_apply(
    body: HeadlessApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not body.dry_run:
        quota = check_apply_quota(db, current_user.id, requested=1)
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
    if not body.dry_run:
        quota = check_apply_quota(db, current_user.id, requested=len(body.application_ids))
        if not quota["allowed"]:
            raise HTTPException(status_code=429, detail=quota)
    task = apply_batch.delay(
        current_user.id,
        body.application_ids,
        auto_submit=body.auto_submit,
        dry_run=body.dry_run,
        max_per_batch=min(body.max_per_batch, 100),
    )
    return {
        "ok": True,
        "queued": True,
        "task_id": task.id,
        "count": len(body.application_ids),
        "message": "Batch headless apply queued for scale processing",
    }


@router.get("/quota")
async def apply_quota(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return check_apply_quota(db, current_user.id, requested=0)


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
    return await messaging_service.handle_inbound(body.channel, body.from_number, body.body, ctx)
