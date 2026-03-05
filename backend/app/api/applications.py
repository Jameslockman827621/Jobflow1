from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.application import Application
from app.models.job import Job
from app.core.security import get_current_user
from app.models.user import User
from app.tasks.applications import prepare_application
from app.tasks.notifications import send_application_confirmation_task
from app.services.matching import JobMatcher

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    job_title: str
    company: str
    status: str
    stage: str
    match_score: Optional[float] = None
    cover_letter: Optional[str] = None
    submitted_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreateApplication(BaseModel):
    job_id: int
    auto_prepare: bool = True  # Trigger AI CV/cover letter generation


class ApplicationCreateResponse(BaseModel):
    id: int
    job_id: int
    status: str
    message: str


@router.get("/", response_model=List[ApplicationResponse])
async def list_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all applications for current user"""
    applications = db.query(Application).filter(
        Application.user_id == current_user.id
    ).order_by(Application.created_at.desc()).all()
    
    return [
        ApplicationResponse(
            id=app.id,
            job_id=app.job_id,
            job_title=app.job.title if app.job else "Unknown",
            company=app.job.company if app.job else "Unknown",
            status=app.status,
            stage=app.stage,
            match_score=app.confidence_score,
            cover_letter=app.cover_letter,
            submitted_at=app.submitted_at,
            created_at=app.created_at,
        )
        for app in applications
    ]


@router.post("/", response_model=ApplicationCreateResponse)
async def create_application(
    data: CreateApplication,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new application for a job"""
    # Verify job exists
    job = db.query(Job).filter(Job.id == data.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check for duplicate
    existing = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.job_id == data.job_id,
    ).first()
    if existing:
        return ApplicationCreateResponse(
            id=existing.id,
            job_id=existing.job_id,
            status=existing.status,
            message="Application already exists",
        )
    
    # Calculate match score
    matcher = JobMatcher(db)
    from app.models.profile import UserProfile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    match_score = matcher.calculate_match_score(profile, job) if profile else 50.0
    
    # Create application
    application = Application(
        user_id=current_user.id,
        job_id=data.job_id,
        status="draft",
        stage="not_started",
        confidence_score=match_score,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    
    # Trigger AI preparation if requested
    message = "Application created"
    if data.auto_prepare:
        prepare_application.delay(application.id)
        message = "Application created - AI is preparing your CV and cover letter"
    
    # Send confirmation email
    send_application_confirmation_task.delay(application.id)
    
    return ApplicationCreateResponse(
        id=application.id,
        job_id=application.job_id,
        status=application.status,
        message=message,
    )


@router.patch("/{app_id}")
async def update_application(
    app_id: int,
    status: Optional[str] = None,
    stage: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update application status, stage, or notes"""
    application = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == current_user.id,
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if status:
        application.status = status
    if stage:
        application.stage = stage
    if notes:
        application.internal_notes = notes
    
    db.commit()
    db.refresh(application)
    
    return {"status": "updated", "application_id": app_id}


@router.post("/{app_id}/apply")
async def submit_application(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit an application - triggers AI to tailor CV and cover letter if not done.
    """
    application = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == current_user.id,
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check if CV and cover letter are ready
    if not application.cover_letter:
        # Trigger AI preparation
        prepare_application.delay(application.id)
        return {
            "status": "preparing",
            "message": "AI is preparing your CV and cover letter. Check back in a moment.",
        }
    
    # Mark as submitted
    from datetime import datetime
    application.status = "submitted"
    application.stage = "applied"
    application.submitted_at = datetime.utcnow()
    db.commit()
    
    return {
        "status": "submitted",
        "message": "Application submitted successfully!",
        "application_id": app_id,
    }


@router.get("/{app_id}/match-score")
async def get_match_score(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed match score breakdown for an application"""
    application = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == current_user.id,
    ).first()
    if not application or not application.job:
        raise HTTPException(status_code=404, detail="Application not found")
    
    from app.models.profile import UserProfile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    matcher = JobMatcher(db)
    score = matcher.calculate_match_score(profile, application.job)
    
    return {
        "application_id": app_id,
        "job_id": application.job_id,
        "overall_score": score,
        "breakdown": {
            "skills": matcher._skills_match(profile, application.job),
            "seniority": matcher._seniority_match(profile, application.job),
            "location": matcher._location_match(profile, application.job),
            "salary": matcher._salary_match(profile, application.job),
        }
    }
