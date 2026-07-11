"""
Application Tracking API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models.application import Application
from app.models.job import Job
from app.models.cv import CV
from app.models.user import User
from app.api.auth import get_current_user
from app.tasks.notifications import send_application_confirmation_task
from app.services.cv_tailor import tailor_cv_for_job, score_cv_against_job

router = APIRouter(tags=["Applications"])


class StartApplicationRequest(BaseModel):
    job_id: int


class TailorCVRequest(BaseModel):
    cv_id: int
    job_id: int


@router.get("")
async def get_applications(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all applications for current user"""
    query = db.query(Application).filter(Application.user_id == current_user.id)

    if status:
        query = query.filter(Application.status == status)

    applications = query.order_by(Application.created_at.desc()).all()

    result = []
    for app in applications:
        job = db.query(Job).filter(Job.id == app.job_id).first()
        result.append({
            "id": app.id,
            "job_id": app.job_id,
            "cv_id": app.cv_id,
            "status": app.status,
            "stage": app.stage,
            "applied_via": app.applied_via,
            "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
            "created_at": app.created_at.isoformat() if app.created_at else None,
            "internal_notes": app.internal_notes,
            "interview_count": app.interview_count,
            "outcome": app.outcome,
            "confidence_score": app.confidence_score,
            "ats_score": app.ats_score,
            "ats_keyword_score": app.ats_keyword_score,
            "ats_skills_score": app.ats_skills_score,
            "ats_experience_score": app.ats_experience_score,
            "tailored_cv_url": app.tailored_cv_url,
            "has_tailored_cv": app.tailored_cv_data is not None,
            "tailoring_method": (app.tailored_cv_data or {}).get("tailoring_method") if app.tailored_cv_data else None,
            "job": {
                "title": job.title if job else "Unknown",
                "company": job.company if job else "Unknown",
                "location": job.location if job else "",
                "external_url": job.external_url if job else "",
            } if job else None,
        })

    return {
        "applications": result,
        "total": len(result)
    }


def _tailor_and_score(application: Application, cv: CV, job: Job, db: Session) -> Dict:
    """Generate a tailored CV for this job, score it, and persist on the application.

    Returns the tailored CV dict + score breakdown.
    """
    # Tailor
    tailored = tailor_cv_for_job(
        cv=cv,
        job_description=job.description or "",
        job_title=job.title or "",
        company=job.company or "",
    )
    # Score
    score = score_cv_against_job(tailored, job.description or "")

    application.tailored_cv_data = tailored
    application.tailored_summary = tailored.get("summary")
    application.tailored_cv_url = f"/api/v1/applications/{application.id}/tailored-cv"
    application.ats_score = score["overall"]
    application.ats_keyword_score = score["keyword_score"]
    application.ats_skills_score = score["skills_score"]
    application.ats_experience_score = score["experience_score"]
    application.confidence_score = score["overall"] / 100.0  # 0-1 range for confidence
    db.commit()
    db.refresh(application)
    return {"tailored_cv": tailored, "score": score}


@router.post("/start")
async def start_application(
    body: StartApplicationRequest = Body(...),
    cv_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a new application — tailors the CV, scores it, and returns the package."""
    job_id = body.job_id
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get CV (use user's primary CV if not specified)
    if cv_id:
        cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
        if not cv:
            raise HTTPException(status_code=404, detail="CV not found")
    else:
        cv = db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.created_at.desc()).first()
        if not cv:
            raise HTTPException(status_code=400, detail="No CV found. Please create a CV first.")

    # Create application record
    application = Application(
        user_id=current_user.id,
        job_id=job_id,
        cv_id=cv.id,
        status="in_progress",
        stage="not_started",
        applied_via="manual"
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    # Tailor the CV for this specific job + score it
    try:
        tailored_result = _tailor_and_score(application, cv, job, db)
        score = tailored_result["score"]
        tailored = tailored_result["tailored_cv"]
    except Exception as e:
        print(f"  start_application: tailor error: {e}")
        score = {"overall": 0, "keyword_score": 0, "skills_score": 0, "experience_score": 0,
                 "matched_keywords": [], "missing_keywords": [], "matched_skills": [],
                 "missing_skills": [], "recommendations": []}
        tailored = None

    cv_download_url = f"/api/v1/applications/{application.id}/tailored-cv" if tailored else f"/api/v1/cvs/{cv.id}/export"
    tips = generate_application_tips(job)

    return {
        "application_id": application.id,
        "cv_download_url": cv_download_url,
        "job_url": job.external_url,
        "job_title": job.title,
        "company": job.company,
        "application_tips": tips,
        "ats_score": score["overall"],
        "ats_breakdown": score,
        "tailoring_method": tailored.get("tailoring_method") if tailored else "none",
        "tailored_summary": tailored.get("summary") if tailored else None,
        "status": "in_progress"
    }


@router.get("/stats/summary")
async def get_application_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get application statistics"""
    applications = db.query(Application).filter(Application.user_id == current_user.id).all()
    stats = {
        "total": len(applications),
        "by_status": {},
        "by_stage": {},
        "submitted": len([a for a in applications if a.status == "submitted"]),
        "interviews": len([a for a in applications if a.stage in ["phone_screen", "technical", "onsite"]]),
        "offers": len([a for a in applications if a.stage == "offer"])
    }
    for app in applications:
        stats["by_status"][app.status] = stats["by_status"].get(app.status, 0) + 1
        stats["by_stage"][app.stage] = stats["by_stage"].get(app.stage, 0) + 1
    return stats


@router.post("/batch-start")
async def batch_start_applications(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start applications for multiple jobs at once.

    For each job, this generates a hyper-personalized, ATS-optimized tailored CV
    and scores it against the job description. The tailored CV is stored on the
    application and can be downloaded via /applications/{id}/tailored-cv.
    """
    job_ids = body.get("job_ids", [])
    if not job_ids:
        raise HTTPException(status_code=400, detail="No jobs selected")
    cv = db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.created_at.desc()).first()
    if not cv:
        raise HTTPException(status_code=400, detail="No CV found. Please create a CV first.")
    results = []
    for job_id in job_ids:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            continue
        existing = db.query(Application).filter(
            Application.user_id == current_user.id, Application.job_id == job_id
        ).first()
        if existing:
            # Re-tailor if not yet tailored (so users can re-run on existing apps)
            score_summary = {
                "overall": existing.ats_score or 0,
                "keyword_score": existing.ats_keyword_score or 0,
                "skills_score": existing.ats_skills_score or 0,
                "experience_score": existing.ats_experience_score or 0,
            }
            results.append({
                "job_id": job_id, "status": "already_applied", "application_id": existing.id,
                "job_url": job.external_url, "job_title": job.title, "company": job.company,
                "ats_score": existing.ats_score,
                "ats_breakdown": score_summary,
                "tailored_cv_url": existing.tailored_cv_url or f"/api/v1/applications/{existing.id}/tailored-cv",
                "tailoring_method": (existing.tailored_cv_data or {}).get("tailoring_method") if existing.tailored_cv_data else "none",
            })
            continue
        application = Application(user_id=current_user.id, job_id=job_id, cv_id=cv.id,
            status="ready_to_apply", stage="not_started", applied_via="extension")
        db.add(application)
        db.commit()
        db.refresh(application)

        # Tailor the CV for this specific job + score it
        try:
            tailored_result = _tailor_and_score(application, cv, job, db)
            score = tailored_result["score"]
            tailored = tailored_result["tailored_cv"]
            ats_score = score["overall"]
            tailoring_method = tailored.get("tailoring_method", "none")
        except Exception as e:
            print(f"  batch_start: tailor error for job {job_id}: {e}")
            score = None
            tailored = None
            ats_score = 0
            tailoring_method = "none"

        results.append({
            "job_id": job_id,
            "application_id": application.id,
            "status": "ready",
            "job_url": job.external_url,
            "job_title": job.title,
            "company": job.company,
            "cv_download_url": f"/api/v1/applications/{application.id}/tailored-cv" if tailored else f"/api/v1/cvs/{cv.id}/export",
            "tailored_cv_url": f"/api/v1/applications/{application.id}/tailored-cv" if tailored else None,
            "ats_score": ats_score,
            "ats_breakdown": score,
            "tailoring_method": tailoring_method,
            "tailored_summary": tailored.get("summary") if tailored else None,
            "application_tips": generate_application_tips(job),
        })
    return {"applications": results, "total": len(results)}


@router.get("/ready-to-apply")
async def get_ready_to_apply(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get applications ready for auto-apply (used by extension)"""
    applications = db.query(Application).filter(
        Application.user_id == current_user.id, Application.status == "ready_to_apply"
    ).all()
    results = []
    for app in applications:
        job = db.query(Job).filter(Job.id == app.job_id).first()
        if job:
            results.append({"application_id": app.id, "job_id": job.id,
                "job_title": job.title, "company": job.company,
                "job_url": job.external_url, "source": job.source.name if job.source else "unknown",
                "cv_download_url": f"/api/v1/cvs/{app.cv_id}/export"})
    return {"applications": results, "total": len(results)}


@router.get("/{application_id}")
async def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific application"""
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return application


@router.put("/{application_id}")
async def update_application(
    application_id: int,
    status: Optional[str] = None,
    stage: Optional[str] = None,
    internal_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update application status/notes — sends email notifications on stage changes."""
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    old_stage = application.stage
    old_status = application.status

    # Update fields
    if status:
        application.status = status
        if status == "submitted":
            application.submitted_at = datetime.utcnow()

    if stage:
        application.stage = stage
        # Track interview count
        if stage in ("phone_screen", "technical", "onsite") and old_stage not in ("phone_screen", "technical", "onsite"):
            application.interview_count = (application.interview_count or 0) + 1

    if internal_notes:
        application.internal_notes = internal_notes

    db.commit()
    db.refresh(application)

    # Send email notifications on stage transitions
    job = db.query(Job).filter(Job.id == application.job_id).first()
    if job and stage and stage != old_stage:
        try:
            from app.services.email import email_service
            if stage in ("phone_screen", "technical", "onsite"):
                email_service.send_interview_notification(
                    to=current_user.email,
                    job_title=job.title,
                    company=job.company,
                    details=f"You moved this application to '{stage.replace('_', ' ')}' stage. Log in to update details and prepare.",
                )
            elif stage == "offer":
                email_service.send_email(
                    to=current_user.email,
                    subject=f"🎉 Offer Received: {job.title} at {job.company}",
                    html_content=f"""
                    <html><body style="font-family:Arial,sans-serif;line-height:1.6;color:#333;max-width:600px;margin:0 auto;">
                    <div style="background:linear-gradient(135deg,#059669,#10b981);color:white;padding:30px;border-radius:12px 12px 0 0;text-align:center;">
                    <h1 style="margin:0;font-size:24px;">Congratulations! 🎉</h1>
                    <p style="margin:8px 0 0 0;opacity:0.9;">You received an offer for {job.title} at {job.company}</p>
                    </div>
                    <div style="padding:25px;background:white;border:1px solid #e5e7eb;border-top:none;">
                    <p>This is amazing news! Take a moment to celebrate, then:</p>
                    <ol>
                    <li>Review the offer carefully (salary, benefits, start date)</li>
                    <li>Prepare any questions you have for the recruiter</li>
                    <li>You usually have 3-5 days to respond</li>
                    </ol>
                    <p style="margin-top:25px;text-align:center;">
                    <a href="http://localhost:3000/kanban" style="background-color:#059669;color:white;padding:14px 28px;text-decoration:none;border-radius:8px;display:inline-block;font-weight:600;">View in Tracker</a>
                    </p>
                    </div>
                    <div style="padding:15px;text-align:center;color:#9ca3af;font-size:12px;">The JobScale Team</div>
                    </body></html>
                    """,
                )
        except Exception as e:
            print(f"  Email notification error (non-blocking): {e}")

    return application


@router.post("/{application_id}/submit")
async def submit_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark application as submitted"""
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    application.status = "submitted"
    application.stage = "applied"
    application.submitted_at = datetime.utcnow()

    db.commit()
    try:
        job = db.query(Job).filter(Job.id == application.job_id).first()
        if job:
            send_application_confirmation_task.delay(application.id)
    except Exception:
        pass  # Don't fail submission if email fails
    db.refresh(application)

    return {
        "message": "Application marked as submitted",
        "application": application
    }


@router.get("/{application_id}/tailored-cv")
async def export_tailored_cv(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export the per-job tailored CV as HTML (for download / extension auto-apply)."""
    from fastapi.responses import HTMLResponse
    from app.api.cvs import render_cv_html
    from app.services.cv_templates import get_template

    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id,
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    if not application.tailored_cv_data:
        raise HTTPException(status_code=404, detail="No tailored CV generated for this application")

    tailored = application.tailored_cv_data
    template = get_template(tailored.get("template_id") or "modern")

    # Build a lightweight shim object compatible with render_cv_html
    class _CVShim:
        pass
    cv_shim = _CVShim()
    for k, v in tailored.items():
        setattr(cv_shim, k, v)
    # render_cv_html expects cv.experience/education/skills/etc — already set above
    cv_shim.full_name = tailored.get("full_name") or ""
    cv_shim.email = tailored.get("email") or ""
    cv_shim.phone = tailored.get("phone") or ""
    cv_shim.location = tailored.get("location") or ""
    cv_shim.linkedin_url = tailored.get("linkedin_url") or ""
    cv_shim.portfolio_url = tailored.get("portfolio_url") or ""
    cv_shim.summary = tailored.get("summary") or ""
    cv_shim.experience = tailored.get("experience") or []
    cv_shim.education = tailored.get("education") or []
    cv_shim.skills = tailored.get("skills") or []
    cv_shim.certifications = tailored.get("certifications") or []
    cv_shim.template_id = tailored.get("template_id") or "modern"

    html_content = render_cv_html(cv_shim, template["html"])
    filename = (tailored.get("full_name") or "cv").replace(" ", "_")
    return HTMLResponse(content=html_content, headers={
        "Content-Disposition": f'attachment; filename="tailored_cv_{filename}_{application_id}.html"'
    })


@router.get("/{application_id}/ats-score")
async def get_application_ats_score(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the ATS score breakdown for an application (re-scores live if missing)."""
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id,
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    job = db.query(Job).filter(Job.id == application.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Re-score live using the stored tailored CV
    if application.tailored_cv_data:
        score = score_cv_against_job(application.tailored_cv_data, job.description or "")
        return {"application_id": application.id, "job_id": job.id, "ats": score}
    return {
        "application_id": application.id,
        "job_id": job.id,
        "ats": {
            "overall": application.ats_score or 0,
            "keyword_score": application.ats_keyword_score or 0,
            "skills_score": application.ats_skills_score or 0,
            "experience_score": application.ats_experience_score or 0,
            "matched_keywords": [], "missing_keywords": [],
            "matched_skills": [], "missing_skills": [],
            "recommendations": ["Re-tailor this CV to see detailed scoring."],
        }
    }


@router.post("/tailor")
async def tailor_cv_for_job_endpoint(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually (re-)tailor a CV for a specific job and return the result + score.

    Body: {"cv_id": 1, "job_id": 2}
    """
    cv_id = body.get("cv_id")
    job_id = body.get("job_id")
    if not cv_id or not job_id:
        raise HTTPException(status_code=400, detail="cv_id and job_id are required")

    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    tailored = tailor_cv_for_job(cv, job.description or "", job.title or "", job.company or "")
    score = score_cv_against_job(tailored, job.description or "")

    return {
        "cv_id": cv.id,
        "job_id": job.id,
        "job_title": job.title,
        "company": job.company,
        "tailored_cv": tailored,
        "ats_score": score,
    }


@router.delete("/{application_id}")
async def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete application"""
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db.delete(application)
    db.commit()
    
    return {"message": "Application deleted"}


def generate_application_tips(job: Job) -> list:
    """Generate application tips based on job source"""
    tips = []

    src_name = ""
    try:
        if job.source is not None and getattr(job.source, "name", None):
            src_name = (job.source.name or "").lower()
    except Exception:
        src_name = ""

    # Source-specific tips
    if "linkedin" in src_name:
        tips.extend([
            "LinkedIn Easy Apply: Your profile will be attached automatically",
            "Make sure your LinkedIn profile is up to date",
            "Consider adding a note to the recruiter (2-3 sentences)"
        ])
    elif "indeed" in src_name:
        tips.extend([
            "Indeed Quick Apply uses your Indeed resume",
            "Upload your tailored CV for better results",
            "Indeed may ask pre-screening questions - be ready"
        ])
    elif "greenhouse" in src_name:
        tips.extend([
            "Greenhouse forms typically ask for LinkedIn profile",
            "They may have custom questions - read carefully",
            "Upload both CV and cover letter if possible"
        ])
    elif "lever" in src_name:
        tips.extend([
            "Lever applications are usually straightforward",
            "They value culture fit - research the company",
            "Include links to portfolio/GitHub if relevant"
        ])
    elif "curated" in src_name:
        tips.extend([
            "This is a sample listing for trying JobScale — replace with live roles once scrapers are configured",
            "Use the external link to practice your application flow",
        ])
    else:
        tips.extend([
            "Company website application - read instructions carefully",
            "Tailor your CV to match the job description",
            "Include a cover letter if the option is available"
        ])
    
    # General tips
    tips.extend([
        "Double-check all fields before submitting",
        "Save a copy of your application for follow-up",
        "Note the date so you can follow up in 1-2 weeks"
    ])
    
    return tips
