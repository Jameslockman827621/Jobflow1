"""
Auto-Apply API — the "Approve-and-Go" queue.

Flow:
  1. User shortlists jobs on the dashboard and clicks "Approve Selected".
  2. Each approved job gets a tailored CV generated + ATS score, then enters
     the queue with status='approved'.
  3. User opens /apply (the queue page) and clicks "Start applying".
  4. Frontend calls /auto-apply/queue/next to get the next approved job.
  5. Frontend opens the job's external_url; the extension content script
     auto-fills the form + attaches the tailored PDF CV.
  6. User reviews and clicks Submit on the form.
  7. Frontend calls /auto-apply/queue/{id}/complete to mark it as applied
     and move to the next job.

The user is always in control — we never auto-submit. We just remove all the
friction (form filling, CV tailoring, PDF generation, common Q&A) so each
application takes ~30 seconds instead of 5-10 minutes.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.job import Job
from app.models.cv import CV
from app.models.auto_apply import UserAutoApplyJob
from app.models.application import Application
from app.api.auth import get_current_user
from app.services.cv_tailor import tailor_cv_for_job, score_cv_against_job

router = APIRouter(tags=["Auto-Apply"])


def _serialize_queue_item(item: UserAutoApplyJob, job: Job) -> Dict[str, Any]:
    """Serialize a queue item + its job into a dict for the frontend/extension."""
    return {
        "id": item.id,
        "job_id": item.job_id,
        "status": item.status,
        "ats_score": item.ats_score,
        "approved_at": item.approved_at.isoformat() if item.approved_at else None,
        "started_at": item.started_at.isoformat() if item.started_at else None,
        "applied_at": item.applied_at.isoformat() if item.applied_at else None,
        "tailored_cv_url": f"/api/v1/auto-apply/queue/{item.id}/tailored-cv",
        "tailored_cv_pdf_url": f"/api/v1/auto-apply/queue/{item.id}/tailored-cv.pdf",
        "job": {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "external_url": job.external_url,
            "description": (job.description or "")[:500],
            "source": job.source.name if job.source else "unknown",
        } if job else None,
    }


# ===== APPROVE FLOW =====

@router.post("/approve")
async def approve_jobs(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a batch of jobs for the application queue.

    For each job, generates a tailored CV + ATS score, then adds it to the queue
    with status='approved'. Skips jobs already in the queue.

    Body: {"job_ids": [1, 2, 3]}
    """
    job_ids = body.get("job_ids", [])
    if not job_ids:
        raise HTTPException(status_code=400, detail="No job_ids provided")

    # Get the user's primary CV (required for tailoring)
    cv = db.query(CV).filter(CV.user_id == current_user.id, CV.is_primary == True).first()
    if not cv:
        cv = db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.created_at.desc()).first()
    if not cv:
        raise HTTPException(status_code=400, detail="No CV found. Please upload a CV first.")

    results = []
    for job_id in job_ids:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            results.append({"job_id": job_id, "status": "not_found"})
            continue

        existing = db.query(UserAutoApplyJob).filter(
            UserAutoApplyJob.user_id == current_user.id,
            UserAutoApplyJob.job_id == job_id,
        ).first()

        if existing:
            # If it was skipped or applied, reset to approved AND re-tailor so the
            # user gets a fresh CV (their CV may have been updated since the first
            # approval, or the previous tailoring may have failed).
            if existing.status in ("skipped", "applied"):
                existing.status = "approved"
                existing.approved_at = datetime.utcnow()
                existing.skipped_at = None
                existing.applied_at = None
                # Re-tailor the CV
                try:
                    tailored = tailor_cv_for_job(cv, job.description or "", job.title or "", job.company or "")
                    score = score_cv_against_job(tailored, job.description or "")
                    existing.tailored_cv_data = tailored
                    existing.ats_score = score["overall"]
                except Exception as e:
                    print(f"  approve: re-tailor error for job {job_id}: {e}")
                db.commit()
            results.append({
                "job_id": job_id, "status": "already_in_queue",
                "queue_id": existing.id, "queue_status": existing.status,
            })
            continue

        # Tailor the CV for this job
        try:
            tailored = tailor_cv_for_job(cv, job.description or "", job.title or "", job.company or "")
            score = score_cv_against_job(tailored, job.description or "")
            ats_score = score["overall"]
        except Exception as e:
            print(f"  approve: tailor error for job {job_id}: {e}")
            tailored = None
            score = None
            ats_score = 0

        item = UserAutoApplyJob(
            user_id=current_user.id,
            job_id=job_id,
            status="approved",
            tailored_cv_data=tailored,
            ats_score=ats_score,
            approved_at=datetime.utcnow(),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        results.append({
            "job_id": job_id, "status": "approved", "queue_id": item.id,
            "ats_score": ats_score,
        })

    return {"results": results, "total": len(results)}


# ===== QUEUE ENDPOINTS =====

@router.get("/jobs")
async def get_auto_apply_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of all jobs in the user's auto-apply queue (any status)."""
    items = db.query(UserAutoApplyJob).filter(
        UserAutoApplyJob.user_id == current_user.id
    ).order_by(UserAutoApplyJob.approved_at.desc()).all()

    job_ids = [i.job_id for i in items]
    jobs = {j.id: j for j in db.query(Job).filter(Job.id.in_(job_ids)).all()} if job_ids else {}

    return {
        "jobs": [_serialize_queue_item(item, jobs.get(item.job_id)) for item in items],
        "total": len(items),
    }


@router.get("/queue")
async def get_queue(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the user's approval queue, optionally filtered by status."""
    q = db.query(UserAutoApplyJob).filter(UserAutoApplyJob.user_id == current_user.id)
    if status:
        q = q.filter(UserAutoApplyJob.status == status)
    items = q.order_by(UserAutoApplyJob.approved_at.asc()).all()

    job_ids = [i.job_id for i in items]
    jobs = {j.id: j for j in db.query(Job).filter(Job.id.in_(job_ids)).all()} if job_ids else {}

    queue = [_serialize_queue_item(item, jobs.get(item.job_id)) for item in items]
    # Summary counts
    counts = {"approved": 0, "in_progress": 0, "applied": 0, "skipped": 0}
    for item in items:
        counts[item.status] = counts.get(item.status, 0) + 1

    return {"queue": queue, "total": len(queue), "counts": counts}


@router.get("/queue/next")
async def get_next_in_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the next 'approved' job in the queue (oldest first)."""
    item = db.query(UserAutoApplyJob).filter(
        UserAutoApplyJob.user_id == current_user.id,
        UserAutoApplyJob.status == "approved",
    ).order_by(UserAutoApplyJob.approved_at.asc()).first()

    if not item:
        return {"queue_item": None, "message": "Queue is empty. Approve some jobs first."}

    job = db.query(Job).filter(Job.id == item.job_id).first()
    return {"queue_item": _serialize_queue_item(item, job)}


@router.post("/queue/{queue_id}/start")
async def start_queue_item(
    queue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a queue item as 'in_progress' (user is currently applying to it)."""
    item = db.query(UserAutoApplyJob).filter(
        UserAutoApplyJob.id == queue_id,
        UserAutoApplyJob.user_id == current_user.id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    # Only allow starting from 'approved' status to prevent restarting
    # already-applied or skipped items
    if item.status not in ("approved", "in_progress"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start a queue item with status '{item.status}'. Only approved items can be started."
        )
    if item.status != "in_progress":
        item.status = "in_progress"
        item.started_at = datetime.utcnow()
        db.commit()
        db.refresh(item)

    job = db.query(Job).filter(Job.id == item.job_id).first()
    return {"queue_item": _serialize_queue_item(item, job)}


@router.post("/queue/{queue_id}/complete")
async def complete_queue_item(
    queue_id: int,
    body: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a queue item as 'applied' and create an Application record.

    Body (optional): {"notes": "...", "skip": false}
    """
    item = db.query(UserAutoApplyJob).filter(
        UserAutoApplyJob.id == queue_id,
        UserAutoApplyJob.user_id == current_user.id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    # Idempotency: don't let a double-submit create a duplicate Application
    if item.status == "applied":
        # Return the next item anyway so the frontend can move on
        next_item = db.query(UserAutoApplyJob).filter(
            UserAutoApplyJob.user_id == current_user.id,
            UserAutoApplyJob.status == "approved",
        ).order_by(UserAutoApplyJob.approved_at.asc()).first()
        job = db.query(Job).filter(Job.id == item.job_id).first()
        next_queue_item = None
        if next_item:
            next_job = db.query(Job).filter(Job.id == next_item.job_id).first()
            next_queue_item = _serialize_queue_item(next_item, next_job)
        return {
            "completed": _serialize_queue_item(item, job),
            "next": next_queue_item,
            "message": "Already marked as applied",
        }

    body = body or {}
    skip = body.get("skip", False)
    notes = body.get("notes")

    if notes:
        item.notes = notes

    if skip:
        item.status = "skipped"
        item.skipped_at = datetime.utcnow()
    else:
        item.status = "applied"
        item.applied_at = datetime.utcnow()
        # Create an Application record so it shows up in the Kanban tracker
        cv = db.query(CV).filter(CV.user_id == current_user.id, CV.is_primary == True).first()
        if not cv:
            cv = db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.created_at.desc()).first()

        # Upsert: don't create duplicate applications
        existing_app = db.query(Application).filter(
            Application.user_id == current_user.id,
            Application.job_id == item.job_id,
        ).first()
        if existing_app:
            existing_app.status = "submitted"
            existing_app.stage = "applied"
            existing_app.submitted_at = datetime.utcnow()
            existing_app.applied_via = "approve_queue"
            if item.tailored_cv_data and not existing_app.tailored_cv_data:
                existing_app.tailored_cv_data = item.tailored_cv_data
                existing_app.ats_score = item.ats_score
        else:
            app = Application(
                user_id=current_user.id,
                job_id=item.job_id,
                cv_id=cv.id if cv else None,
                status="submitted",
                stage="applied",
                applied_via="approve_queue",
                submitted_at=datetime.utcnow(),
                tailored_cv_data=item.tailored_cv_data,
                ats_score=item.ats_score,
            )
            db.add(app)

    db.commit()
    db.refresh(item)
    job = db.query(Job).filter(Job.id == item.job_id).first()

    # Return the next item in the queue so the frontend can immediately move on
    next_item = db.query(UserAutoApplyJob).filter(
        UserAutoApplyJob.user_id == current_user.id,
        UserAutoApplyJob.status == "approved",
    ).order_by(UserAutoApplyJob.approved_at.asc()).first()
    next_queue_item = None
    if next_item:
        next_job = db.query(Job).filter(Job.id == next_item.job_id).first()
        next_queue_item = _serialize_queue_item(next_item, next_job)

    return {
        "completed": _serialize_queue_item(item, job),
        "next": next_queue_item,
    }


@router.delete("/queue/{queue_id}")
async def remove_from_queue(
    queue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a job from the queue entirely."""
    item = db.query(UserAutoApplyJob).filter(
        UserAutoApplyJob.id == queue_id,
        UserAutoApplyJob.user_id == current_user.id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    db.delete(item)
    db.commit()
    return {"message": "Removed from queue"}


# ===== TAILORED CV EXPORT (HTML + PDF) =====

@router.get("/queue/{queue_id}/tailored-cv")
async def export_queue_tailored_cv(
    queue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export the tailored CV for a queue item as HTML."""
    from fastapi.responses import HTMLResponse
    from app.api.cvs import render_cv_html
    from app.services.cv_templates import get_template

    item = db.query(UserAutoApplyJob).filter(
        UserAutoApplyJob.id == queue_id,
        UserAutoApplyJob.user_id == current_user.id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    if not item.tailored_cv_data:
        raise HTTPException(status_code=404, detail="No tailored CV for this item")

    tailored = item.tailored_cv_data
    template = get_template(tailored.get("template_id") or "modern")

    class _Shim:
        pass
    shim = _Shim()
    for k, v in tailored.items():
        setattr(shim, k, v)
    shim.full_name = tailored.get("full_name") or ""
    shim.email = tailored.get("email") or ""
    shim.phone = tailored.get("phone") or ""
    shim.location = tailored.get("location") or ""
    shim.linkedin_url = tailored.get("linkedin_url") or ""
    shim.portfolio_url = tailored.get("portfolio_url") or ""
    shim.summary = tailored.get("summary") or ""
    shim.experience = tailored.get("experience") or []
    shim.education = tailored.get("education") or []
    shim.skills = tailored.get("skills") or []
    shim.certifications = tailored.get("certifications") or []
    shim.template_id = tailored.get("template_id") or "modern"

    html_content = render_cv_html(shim, template["html"])
    return HTMLResponse(content=html_content, headers={
        "Content-Disposition": f'inline; filename="tailored_cv_{queue_id}.html"'
    })


@router.get("/queue/{queue_id}/tailored-cv.pdf")
async def export_queue_tailored_cv_pdf(
    queue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export the tailored CV for a queue item as PDF (for uploading to ATS forms)."""
    from weasyprint import HTML
    from app.api.cvs import render_cv_html
    from app.services.cv_templates import get_template

    item = db.query(UserAutoApplyJob).filter(
        UserAutoApplyJob.id == queue_id,
        UserAutoApplyJob.user_id == current_user.id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    if not item.tailored_cv_data:
        raise HTTPException(status_code=404, detail="No tailored CV for this item")

    tailored = item.tailored_cv_data
    template = get_template(tailored.get("template_id") or "modern")

    class _Shim:
        pass
    shim = _Shim()
    for k, v in tailored.items():
        setattr(shim, k, v)
    shim.full_name = tailored.get("full_name") or ""
    shim.email = tailored.get("email") or ""
    shim.phone = tailored.get("phone") or ""
    shim.location = tailored.get("location") or ""
    shim.linkedin_url = tailored.get("linkedin_url") or ""
    shim.portfolio_url = tailored.get("portfolio_url") or ""
    shim.summary = tailored.get("summary") or ""
    shim.experience = tailored.get("experience") or []
    shim.education = tailored.get("education") or []
    shim.skills = tailored.get("skills") or []
    shim.certifications = tailored.get("certifications") or []
    shim.template_id = tailored.get("template_id") or "modern"

    html_content = render_cv_html(shim, template["html"])
    try:
        pdf_bytes = HTML(string=html_content).write_pdf()
    except Exception as e:
        print(f"  PDF export error: {e}")
        raise HTTPException(status_code=500, detail="PDF generation failed")

    safe_name = (tailored.get("full_name") or "cv").replace(" ", "_")
    job = db.query(Job).filter(Job.id == item.job_id).first()
    company_part = (job.company or "").replace(" ", "_") if job else ""
    filename = f"tailored_cv_{safe_name}_{company_part}_{item.job_id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ===== LEGACY SINGLE-JOB ENDPOINTS (kept for backward compat) =====

@router.post("/jobs/{job_id}")
async def add_auto_apply_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a single job to the approval queue (legacy endpoint)."""
    job = db.query(Job).filter(Job.id == job_id, Job.is_active == True).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing = db.query(UserAutoApplyJob).filter(
        UserAutoApplyJob.user_id == current_user.id,
        UserAutoApplyJob.job_id == job_id
    ).first()
    if existing:
        return {"message": "Already in queue", "job_id": job_id, "queue_id": existing.id}

    item = UserAutoApplyJob(user_id=current_user.id, job_id=job_id, status="approved")
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"message": "Added to queue", "job_id": job_id, "queue_id": item.id}


@router.delete("/jobs/{job_id}")
async def remove_auto_apply_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a job from the queue (legacy endpoint)."""
    item = db.query(UserAutoApplyJob).filter(
        UserAutoApplyJob.user_id == current_user.id,
        UserAutoApplyJob.job_id == job_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Job not in queue")
    db.delete(item)
    db.commit()
    return {"message": "Removed from queue", "job_id": job_id}


# ===== APPLICATION ANSWERS (for extension auto-fill) =====

@router.get("/answers")
async def get_application_answers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the user's saved answers to common application questions + auto-fill profile.

    The extension uses these to pre-fill forms on Greenhouse/Lever/Ashby/etc.
    """
    from app.models.profile import UserProfile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        return {"answers": {}, "profile": {}}
    return {
        "answers": profile.application_answers or {},
        "profile": profile.application_profile or {},
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "location": profile.location,
    }


@router.put("/answers")
async def update_application_answers(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save the user's answers to common application questions + auto-fill profile.

    Body: {
        "answers": {"work_authorization": "Yes", "requires_sponsorship": "No", ...},
        "profile": {"linkedin_url": "...", "github_url": "...", "website": "...", "cover_letter_default": "..."}
    }
    """
    from app.models.profile import UserProfile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    if "answers" in body:
        profile.application_answers = body["answers"]
    if "profile" in body:
        existing = profile.application_profile or {}
        existing.update(body["profile"])
        profile.application_profile = existing

    db.commit()
    return {
        "answers": profile.application_answers or {},
        "profile": profile.application_profile or {},
        "message": "Application answers saved",
    }