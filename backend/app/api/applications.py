"""
Application Tracking API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.application import Application
from app.models.job import Job
from app.models.cv import CV
from app.models.user import User
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/v1/applications", tags=["Applications"])


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
    
    return {
        "applications": applications,
        "total": len(applications)
    }


@router.post("/start")
async def start_application(
    job_id: int,
    cv_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a new application - generates application package
    
    Returns:
    - Application ID
    - CV download URL
    - Job URL
    - Application tips
    """
    # Get job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get CV (use user's primary CV if not specified)
    if cv_id:
        cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
        if not cv:
            raise HTTPException(status_code=404, detail="CV not found")
    else:
        # Get user's most recent CV
        cv = db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.created_at.desc()).first()
        if not cv:
            raise HTTPException(status_code=400, detail="No CV found. Please create a CV first.")
    
    # Create application record
    application = Application(
        user_id=current_user.id,
        job_id=job_id,
        cv_id=cv.id,
        status="in_progress",  # User started but hasn't submitted yet
        stage="not_started",
        applied_via="manual"  # Will be updated if they use auto-apply later
    )
    
    db.add(application)
    db.commit()
    db.refresh(application)
    
    # Generate application package
    cv_download_url = f"/api/v1/cvs/{cv.id}/export"
    
    # Generate application tips based on job source
    tips = generate_application_tips(job)
    
    return {
        "application_id": application.id,
        "cv_download_url": cv_download_url,
        "job_url": job.external_url,
        "job_title": job.title,
        "company": job.company,
        "application_tips": tips,
        "status": "in_progress"
    }


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
    """Update application status/notes"""
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Update fields
    if status:
        application.status = status
        if status == "submitted":
            application.submitted_at = datetime.utcnow()
    
    if stage:
        application.stage = stage
    
    if internal_notes:
        application.internal_notes = internal_notes
    
    db.commit()
    db.refresh(application)
    
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
    db.refresh(application)
    
    return {
        "message": "Application marked as submitted",
        "application": application
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
    
    # Count by status
    for app in applications:
        stats["by_status"][app.status] = stats["by_status"].get(app.status, 0) + 1
        stats["by_stage"][app.stage] = stats["by_stage"].get(app.stage, 0) + 1
    
    return stats


def generate_application_tips(job: Job) -> list:
    """Generate application tips based on job source"""
    tips = []
    
    # Source-specific tips
    if "linkedin" in (job.source or "").lower():
        tips.extend([
            "LinkedIn Easy Apply: Your profile will be attached automatically",
            "Make sure your LinkedIn profile is up to date",
            "Consider adding a note to the recruiter (2-3 sentences)"
        ])
    elif "indeed" in (job.source or "").lower():
        tips.extend([
            "Indeed Quick Apply uses your Indeed resume",
            "Upload your tailored CV for better results",
            "Indeed may ask pre-screening questions - be ready"
        ])
    elif "greenhouse" in (job.source or "").lower():
        tips.extend([
            "Greenhouse forms typically ask for LinkedIn profile",
            "They may have custom questions - read carefully",
            "Upload both CV and cover letter if possible"
        ])
    elif "lever" in (job.source or "").lower():
        tips.extend([
            "Lever applications are usually straightforward",
            "They value culture fit - research the company",
            "Include links to portfolio/GitHub if relevant"
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
