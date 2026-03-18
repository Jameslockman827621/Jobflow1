"""
Auto-Apply API

Jobs the user selects in the dashboard for auto-apply via the Chrome extension.
The extension fetches this list and auto-applies when the user visits a matching job page.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.job import Job
from app.models.auto_apply import UserAutoApplyJob
from app.api.auth import get_current_user

router = APIRouter(tags=["Auto-Apply"])


@router.get("/jobs")
async def get_auto_apply_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of jobs user has selected for auto-apply.
    Used by the Chrome extension to match against the current page.
    Returns job title, company, external_url for matching.
    """
    selections = db.query(UserAutoApplyJob).filter(
        UserAutoApplyJob.user_id == current_user.id
    ).all()

    job_ids = [s.job_id for s in selections]
    if not job_ids:
        return {"jobs": []}

    jobs = db.query(Job).filter(
        Job.id.in_(job_ids),
        Job.is_active == True
    ).all()

    return {
        "jobs": [
            {
                "id": j.id,
                "title": j.title,
                "company": j.company,
                "external_url": j.external_url,
                "location": j.location,
            }
            for j in jobs
        ]
    }


@router.post("/jobs/{job_id}")
async def add_auto_apply_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a job to the user's auto-apply list."""
    # Verify job exists
    job = db.query(Job).filter(Job.id == job_id, Job.is_active == True).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check if already added
    existing = db.query(UserAutoApplyJob).filter(
        UserAutoApplyJob.user_id == current_user.id,
        UserAutoApplyJob.job_id == job_id
    ).first()
    if existing:
        return {"message": "Already in auto-apply list", "job_id": job_id}

    selection = UserAutoApplyJob(user_id=current_user.id, job_id=job_id)
    db.add(selection)
    db.commit()

    return {"message": "Added to auto-apply", "job_id": job_id}


@router.delete("/jobs/{job_id}")
async def remove_auto_apply_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a job from the user's auto-apply list."""
    selection = db.query(UserAutoApplyJob).filter(
        UserAutoApplyJob.user_id == current_user.id,
        UserAutoApplyJob.job_id == job_id
    ).first()

    if not selection:
        raise HTTPException(status_code=404, detail="Job not in auto-apply list")

    db.delete(selection)
    db.commit()

    return {"message": "Removed from auto-apply", "job_id": job_id}
