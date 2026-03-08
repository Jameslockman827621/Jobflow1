"""
CV/Resume API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

from app.database import get_db
from app.models.cv import CV, CVTemplate
from app.models.user import User
from app.services.cv_builder import cv_builder_service
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/v1/cvs", tags=["CVs"])


@router.get("")
async def get_user_cvs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all CVs for current user"""
    cvs = db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.created_at.desc()).all()
    return {
        "cvs": cvs,
        "total": len(cvs)
    }


@router.get("/{cv_id}")
async def get_cv(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific CV"""
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    return cv


@router.post("")
async def create_cv(
    cv_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new CV"""
    cv = CV(
        user_id=current_user.id,
        full_name=cv_data.get("full_name"),
        email=cv_data.get("email"),
        phone=cv_data.get("phone", ""),
        location=cv_data.get("location", ""),
        linkedin_url=cv_data.get("linkedin_url", ""),
        portfolio_url=cv_data.get("portfolio_url", ""),
        summary=cv_data.get("summary", ""),
        experience=cv_data.get("experience", []),
        education=cv_data.get("education", []),
        skills=cv_data.get("skills", []),
        certifications=cv_data.get("certifications", []),
        projects=cv_data.get("projects", []),
        template_id=cv_data.get("template_id", "modern"),
        is_ai_generated=cv_data.get("is_ai_generated", False)
    )
    
    db.add(cv)
    db.commit()
    db.refresh(cv)
    
    return cv


@router.put("/{cv_id}")
async def update_cv(
    cv_id: int,
    cv_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update existing CV"""
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    
    # Update fields
    for field, value in cv_data.items():
        if hasattr(cv, field) and field not in ['id', 'user_id', 'created_at', 'updated_at']:
            setattr(cv, field, value)
    
    cv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cv)
    
    return cv


@router.delete("/{cv_id}")
async def delete_cv(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete CV"""
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    
    db.delete(cv)
    db.commit()
    
    return {"message": "CV deleted successfully"}


@router.post("/generate-summary")
async def generate_summary(
    experience: List[Dict],
    skills: List[str],
    target_role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI-generate professional summary"""
    summary = await cv_builder_service.generate_summary(experience, skills, target_role)
    return {"summary": summary}


@router.post("/enhance-description")
async def enhance_description(
    role: str,
    company: str,
    description: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI-enhance job description"""
    enhanced = await cv_builder_service.enhance_job_description(role, company, description)
    return {"enhanced_description": enhanced}


@router.post("/tailor-for-job")
async def tailor_for_job(
    cv_id: int,
    job_description: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tailor CV for specific job"""
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    
    cv_data = {
        "summary": cv.summary,
        "experience": cv.experience,
        "skills": cv.skills
    }
    
    tailored = await cv_builder_service.tailor_cv_for_job(cv_data, job_description)
    
    # Update CV with tailored content
    cv.summary = tailored.get('summary', cv.summary)
    db.commit()
    db.refresh(cv)
    
    return cv


@router.get("/{cv_id}/completeness")
async def check_completeness(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check CV completeness score"""
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    
    cv_data = {
        "full_name": cv.full_name,
        "email": cv.email,
        "summary": cv.summary,
        "phone": cv.phone,
        "location": cv.location,
        "linkedin_url": cv.linkedin_url,
        "experience": cv.experience,
        "education": cv.education,
        "skills": cv.skills
    }
    
    result = cv_builder_service.validate_cv_completeness(cv_data)
    return result


@router.get("/templates")
async def get_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available CV templates"""
    templates = db.query(CVTemplate).all()
    return {
        "templates": templates,
        "total": len(templates)
    }


@router.post("/upload")
async def upload_cv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload existing CV (PDF/DOCX)"""
    # Validate file type
    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")
    
    # Save file
    upload_dir = f"uploads/cvs/{current_user.id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = f"{upload_dir}/{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create CV record
    cv = CV(
        user_id=current_user.id,
        full_name=current_user.email.split("@")[0],  # Placeholder
        email=current_user.email,
        file_path=file_path,
        is_ai_generated=False
    )
    
    db.add(cv)
    db.commit()
    db.refresh(cv)
    
    return {
        "cv_id": cv.id,
        "file_path": file_path,
        "message": "CV uploaded successfully. You can now edit the parsed content."
    }
