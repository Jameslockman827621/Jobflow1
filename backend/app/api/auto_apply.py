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

        # Tailor the CV + generate a cover letter for this job
        try:
            tailored = tailor_cv_for_job(cv, job.description or "", job.title or "", job.company or "")
            score = score_cv_against_job(tailored, job.description or "")
            ats_score = score["overall"]
            # Generate a cover letter tailored to this job
            cover_letter = _generate_cover_letter(cv, job, tailored)
        except Exception as e:
            print(f"  approve: tailor error for job {job_id}: {e}")
            tailored = None
            score = None
            ats_score = 0
            cover_letter = None

        item = UserAutoApplyJob(
            user_id=current_user.id,
            job_id=job_id,
            status="approved",
            tailored_cv_data=tailored,
            ats_score=ats_score,
            approved_at=datetime.utcnow(),
        )
        # Store the cover letter in the tailored CV data so it's accessible
        if tailored and cover_letter:
            tailored["cover_letter"] = cover_letter
            item.tailored_cv_data = tailored
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

# ===== COVER LETTER GENERATOR =====

def _generate_cover_letter(cv: CV, job: Job, tailored: dict) -> Optional[str]:
    """Generate a cover letter tailored to this job using the user's real background.

    Uses AI (OpenAI) when available, falls back to a keyword-based template
    that mirrors the job description's keywords naturally.
    """
    from app.core.config import settings

    if settings.OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            cv_payload = {
                "full_name": cv.full_name,
                "skills": cv.skills or [],
                "experience": cv.experience or [],
                "summary": tailored.get("summary") or cv.summary or "",
            }
            prompt = f"""Write a compelling cover letter for this job application.

CANDIDATE: {cv.full_name}
JOB: {job.title} at {job.company}
JOB DESCRIPTION: {(job.description or "")[:2000]}

CANDIDATE BACKGROUND (JSON):
{__import__('json').dumps(cv_payload, indent=2)}

RULES:
1. Keep it under 250 words — recruiters skim cover letters.
2. Show genuine enthusiasm for the company and role.
3. Highlight 2-3 most relevant achievements from the candidate's real experience.
4. Mirror the job description's keywords naturally (don't stuff).
5. Professional but personable tone — not generic, not robotic.
6. Include a brief call to action at the end.
7. Use only real facts from the candidate's background — never fabricate.
8. Output only the cover letter text, no subject line or headers.

Output:"""
            response = client.chat.completions.create(
                model=getattr(settings, "LLM_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.5,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"  cover letter AI error: {e}")

    # Fallback: keyword-based template
    from app.services.cv_tailor import _reorder_skills_by_relevance
    top_skills = _reorder_skills_by_relevance(cv.skills or [], tailored.get("keywords_matched", []))[:4]
    skills_str = ", ".join(top_skills) if top_skills else "software development"

    years = ""
    try:
        from app.services.cv_tailor import _estimate_years_experience
        y = _estimate_years_experience(cv.experience or [])
        if y and y > 0:
            years = f" with {int(y)}+ years of experience"
    except Exception:
        pass

    return f"""Dear Hiring Team at {job.company},

I am excited to apply for the {job.title} position at {job.company}. With my background{years} in {skills_str}, I am confident I can make a meaningful impact on your team.

What draws me to {job.company} is the opportunity to work on challenging problems alongside a talented team. My experience building production systems has taught me how to ship reliably, collaborate cross-functionally, and iterate based on user feedback — skills that align closely with what this role requires.

I would welcome the chance to discuss how my background can contribute to {job.company}'s goals. Thank you for your time and consideration.

Best regards,
{cv.full_name}"""


# ===== RESUME DIFF ENDPOINT =====

@router.get("/queue/{queue_id}/diff")
async def get_resume_diff(
    queue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a line-by-line diff between the user's original CV and the tailored version.

    Shows the user exactly what changed before they approve/send — builds trust
    and lets them catch anything they want to edit.
    """
    import difflib

    item = db.query(UserAutoApplyJob).filter(
        UserAutoApplyJob.id == queue_id,
        UserAutoApplyJob.user_id == current_user.id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    if not item.tailored_cv_data:
        raise HTTPException(status_code=404, detail="No tailored CV for this item")

    # Get the original CV
    cv = db.query(CV).filter(CV.user_id == current_user.id, CV.is_primary == True).first()
    if not cv:
        cv = db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.created_at.desc()).first()
    if not cv:
        raise HTTPException(status_code=404, detail="No original CV found")

    tailored = item.tailored_cv_data

    # Build text representations for diffing
    def _cv_to_lines(cv_obj, data=None):
        lines = []
        d = data or {}
        lines.append(f"Name: {d.get('full_name') or cv_obj.full_name}")
        lines.append(f"Summary: {d.get('summary') or cv_obj.summary or ''}")
        lines.append(f"Skills: {', '.join(d.get('skills') or cv_obj.skills or [])}")
        lines.append("")
        lines.append("Experience:")
        for exp in (d.get("experience") or cv_obj.experience or []):
            lines.append(f"  {exp.get('role', '')} at {exp.get('company', '')} ({exp.get('start_date', '')} - {exp.get('end_date', '')})")
            if exp.get("description"):
                lines.append(f"    {exp['description']}")
        lines.append("")
        lines.append("Education:")
        for edu in (d.get("education") or cv_obj.education or []):
            lines.append(f"  {edu.get('degree', '')} at {edu.get('institution', '')} ({edu.get('graduation_year', '')})")
        return lines

    original_lines = _cv_to_lines(cv)
    tailored_lines = _cv_to_lines(cv, tailored)

    # Generate unified diff
    diff = list(difflib.unified_diff(
        original_lines,
        tailored_lines,
        fromfile="original_cv.txt",
        tofile="tailored_cv.txt",
        lineterm="",
    ))

    # Parse into structured changes for the frontend
    changes = []
    for line in diff:
        if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
            continue
        if line.startswith("+"):
            changes.append({"type": "added", "text": line[1:]})
        elif line.startswith("-"):
            changes.append({"type": "removed", "text": line[1:]})
        elif line.strip():
            changes.append({"type": "context", "text": line})

    return {
        "queue_id": queue_id,
        "changes": changes,
        "raw_diff": "\n".join(diff),
        "has_cover_letter": bool(tailored.get("cover_letter")),
        "cover_letter": tailored.get("cover_letter"),
    }


# ===== APPLICATION RECEIPT ENDPOINT =====

@router.post("/queue/{queue_id}/receipt")
async def submit_receipt(
    queue_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Store what was actually submitted to the ATS — called by the extension after auto-submit.

    Body: {
        "fields_filled": {"name": "James Lock", "email": "james@example.com", ...},
        "answers": {"Why Stripe?": "Because...", ...},
        "resume_file": "tailored_cv_james_lock_stripe.pdf",
        "ats_response": "success",
        "submitted_at": "2026-07-02T20:00:00Z"
    }
    """
    item = db.query(UserAutoApplyJob).filter(
        UserAutoApplyJob.id == queue_id,
        UserAutoApplyJob.user_id == current_user.id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")

    # Also update the Application record if one exists
    from app.models.application import Application
    app = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.job_id == item.job_id,
    ).first()

    receipt = {
        "fields_filled": body.get("fields_filled", {}),
        "answers": body.get("answers", {}),
        "resume_file": body.get("resume_file", ""),
        "ats_response": body.get("ats_response", ""),
        "submitted_at": body.get("submitted_at") or datetime.utcnow().isoformat(),
        "ats_type": body.get("ats_type", "unknown"),
    }

    if app:
        app.submission_receipt = receipt
        app.status = "submitted"
        app.stage = "applied"
        app.submitted_at = datetime.utcnow()
    else:
        # Create the application if it doesn't exist yet
        cv = db.query(CV).filter(CV.user_id == current_user.id, CV.is_primary == True).first()
        app = Application(
            user_id=current_user.id,
            job_id=item.job_id,
            cv_id=cv.id if cv else None,
            status="submitted",
            stage="applied",
            applied_via="auto_submit",
            submitted_at=datetime.utcnow(),
            submission_receipt=receipt,
            tailored_cv_data=item.tailored_cv_data,
            ats_score=item.ats_score,
        )
        db.add(app)

    # Mark the queue item as applied
    item.status = "applied"
    item.applied_at = datetime.utcnow()

    db.commit()

    return {"message": "Receipt stored", "application_id": app.id if app else None}


# ===== AUTO-SUBMIT TOGGLE =====

@router.get("/auto-submit")
async def get_auto_submit_setting(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if the user has enabled auto-submit (the extension clicks Submit for them)."""
    from app.models.profile import UserProfile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    return {"auto_submit_enabled": profile.auto_submit_enabled if profile else False}


@router.put("/auto-submit")
async def set_auto_submit_setting(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enable or disable auto-submit. User must explicitly opt in.

    Body: {"enabled": true}
    When enabled, the Chrome extension will click Submit after filling the form.
    When disabled (default), the user must click Submit themselves.
    """
    from app.models.profile import UserProfile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    profile.auto_submit_enabled = body.get("enabled", False)
    db.commit()

    return {
        "auto_submit_enabled": profile.auto_submit_enabled,
        "message": "Auto-submit enabled — the extension will click Submit for you." if profile.auto_submit_enabled else "Auto-submit disabled — you will click Submit yourself.",
    }


# ===== EMAIL WEBHOOK FOR AUTO-TRACKING =====

@router.post("/emails/inbound")
async def inbound_email_webhook(
    body: dict,
    db: Session = Depends(get_db),
):
    """Webhook for email parsing services (SendGrid Inbound Parse, Postmark, etc.)

    When a recruiter replies to a user's application, the email forwarding
    service POSTs the parsed email here. We match it to the right application
    and auto-update the status.

    Body (from SendGrid Inbound Parse):
    {
        "from": "recruiter@stripe.com",
        "to": "user+apply@jobscale.com",
        "subject": "Interview invitation - Senior Frontend Engineer",
        "text": "Hi James, thanks for applying...",
        "html": "..."
    }

    No auth required — the webhook URL should be kept secret. In production,
    verify the signature from the email parsing service.
    """
    from app.models.application import Application
    from app.models.user import User
    from sqlalchemy import or_
    import re

    sender = (body.get("from") or "").lower()
    subject = (body.get("subject") or "").lower()
    text = (body.get("text") or body.get("html") or "").lower()

    if not sender or not text:
        return {"status": "ignored", "reason": "missing fields"}

    # Detect the type of email based on keywords
    is_interview = any(kw in subject + text for kw in [
        "interview", "schedule a call", "phone screen", "technical interview",
        "onsite", "invite you", "congratulations", "move forward",
    ])
    is_rejection = any(kw in subject + text for kw in [
        "unfortunately", "not moving forward", "regret", "different direction",
        "not selected", "position has been filled",
    ])
    is_offer = any(kw in subject + text for kw in [
        "offer", "congratulations", "pleased to offer", "employment offer",
    ])
    is_viewed = any(kw in subject + text for kw in [
        "thank you for applying", "received your application", "reviewing",
    ])

    # Try to match the email to a user + application
    # Strategy: find applications where the company domain matches the sender domain
    sender_domain = sender.split("@")[-1].split(">")[0] if "@" in sender else ""

    matched_apps = []
    if sender_domain:
        # Search for applications where the job's company name might match the sender domain
        apps = db.query(Application).filter(
            Application.status == "submitted",
        ).all()

        for app in apps:
            job = db.query(Job).filter(Job.id == app.job_id).first()
            if not job:
                continue
            # Check if the company name appears in the sender domain or email
            company_lower = (job.company or "").lower().replace(" ", "")
            if company_lower and (company_lower in sender_domain or sender_domain in company_lower):
                matched_apps.append(app)
            # Also check if the job title appears in the subject
            if job.title and job.title.lower() in subject:
                if app not in matched_apps:
                    matched_apps.append(app)

    if not matched_apps:
        return {"status": "no_match", "reason": "could not match email to any application"}

    # Update the matched applications
    updated = 0
    for app in matched_apps:
        old_stage = app.stage
        if is_offer:
            app.stage = "offer"
        elif is_interview:
            if app.stage not in ("phone_screen", "technical", "onsite", "offer"):
                app.stage = "phone_screen"
            app.interview_count = (app.interview_count or 0) + 1
        elif is_rejection:
            app.stage = "rejected"
            app.outcome = "rejected"
        elif is_viewed and app.stage == "applied":
            app.stage = "applied"  # Keep as applied but mark as viewed
            app.status = "viewed"

        if app.stage != old_stage:
            updated += 1
            # Send notification email to the user
            user = db.query(User).filter(User.id == app.user_id).first()
            job = db.query(Job).filter(Job.id == app.job_id).first()
            if user and job:
                try:
                    from app.services.email import email_service
                    if is_interview:
                        email_service.send_interview_notification(
                            to=user.email,
                            job_title=job.title,
                            company=job.company,
                            details=f"Auto-detected from recruiter email: {body.get('subject', '')}",
                        )
                    elif is_offer:
                        email_service.send_email(
                            to=user.email,
                            subject=f"🎉 Offer Received: {job.title} at {job.company}",
                            html_content=f"<p>Great news! We detected an offer email from {job.company} for {job.title}. Check your inbox for details.</p>",
                        )
                except Exception as e:
                    print(f"  email webhook: notification error: {e}")

    db.commit()

    return {
        "status": "processed",
        "matched_applications": len(matched_apps),
        "updated": updated,
        "detected_type": "offer" if is_offer else "interview" if is_interview else "rejection" if is_rejection else "viewed" if is_viewed else "unknown",
    }


# ===== AUTONOMOUS APPLY SESSION =====

@router.post("/auto-session/start")
async def start_auto_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start an autonomous apply session.

    Returns the list of approved queue items that the extension should process.
    The extension will open each job URL, fill the form, auto-submit (if enabled),
    send a receipt, and move to the next — all without user interaction.

    The user clicks this once, then walks away. The extension does the rest.
    """
    items = db.query(UserAutoApplyJob).filter(
        UserAutoApplyJob.user_id == current_user.id,
        UserAutoApplyJob.status == "approved",
    ).order_by(UserAutoApplyJob.approved_at.asc()).all()

    if not items:
        return {"jobs": [], "total": 0, "message": "No approved jobs to apply to. Approve some jobs first."}

    # Mark all as "in_session" so we can track progress
    session_jobs = []
    for item in items:
        job = db.query(Job).filter(Job.id == item.job_id).first()
        if not job:
            continue
        session_jobs.append({
            "queue_id": item.id,
            "job_id": job.id,
            "job_title": job.title,
            "company": job.company,
            "external_url": job.external_url,
            "ats_score": item.ats_score,
            "tailored_cv_pdf_url": f"{DASHBOARD_URL}/api/v1/auto-apply/queue/{item.id}/tailored-cv.pdf"
        if False else f"/api/v1/auto-apply/queue/{item.id}/tailored-cv.pdf",  # relative — extension prepends DASHBOARD_URL
            "cover_letter": (item.tailored_cv_data or {}).get("cover_letter"),
        })

    return {
        "jobs": session_jobs,
        "total": len(session_jobs),
        "message": f"Starting autonomous session with {len(session_jobs)} jobs. The extension will process them one by one.",
    }


@router.get("/auto-session/status")
async def get_auto_session_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the status of the current autonomous session — how many approved,
    in_progress, applied, skipped."""
    items = db.query(UserAutoApplyJob).filter(
        UserAutoApplyJob.user_id == current_user.id,
    ).all()

    counts = {"approved": 0, "in_progress": 0, "applied": 0, "skipped": 0}
    for item in items:
        counts[item.status] = counts.get(item.status, 0) + 1

    remaining = counts["approved"] + counts["in_progress"]
    return {
        "counts": counts,
        "remaining": remaining,
        "is_active": remaining > 0,
        "message": f"{remaining} jobs remaining in session" if remaining > 0 else "Session complete",
    }


# ===== AUTO-APPROVE SETTINGS =====

@router.get("/auto-approve")
async def get_auto_approve_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get auto-approve settings."""
    from app.models.profile import UserProfile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    return {
        "auto_approve_enabled": profile.auto_approve_enabled if profile else False,
        "auto_approve_threshold": profile.auto_approve_threshold if profile else 60.0,
    }


@router.put("/auto-approve")
async def set_auto_approve_settings(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enable/disable auto-approve and set the ATS score threshold.

    Body: {"enabled": true, "threshold": 70}

    When enabled, the background monitor will automatically approve jobs that:
    1. Match the user's target roles and companies
    2. Have an ATS score >= threshold
    These go straight into the apply queue with tailored CVs — no manual selection needed.
    """
    from app.models.profile import UserProfile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    profile.auto_approve_enabled = body.get("enabled", False)
    if body.get("threshold") is not None:
        profile.auto_approve_threshold = float(body["threshold"])
    db.commit()

    return {
        "auto_approve_enabled": profile.auto_approve_enabled,
        "auto_approve_threshold": profile.auto_approve_threshold,
        "message": "Auto-approve enabled — new matching jobs will be added to your queue automatically." if profile.auto_approve_enabled else "Auto-approve disabled.",
    }
