from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import json

from app.database import SessionLocal
from app.core.security import get_current_user
from app.models.user import User
from app.models.profile import UserProfile, Skill

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SkillInput(BaseModel):
    name: str
    category: Optional[str] = None
    years: Optional[float] = None
    proficiency: Optional[str] = None  # beginner, intermediate, advanced, expert


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    desired_roles: Optional[List[str]] = None
    desired_industries: Optional[List[str]] = None
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    remote_only: Optional[bool] = None
    relocate: Optional[bool] = None
    preferred_countries: Optional[List[str]] = None
    years_of_experience: Optional[float] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    resume_text: Optional[str] = None


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    first_name: Optional[str]
    last_name: Optional[str]
    location: Optional[str]
    timezone: Optional[str]
    desired_roles: List[str]
    desired_industries: List[str]
    min_salary: Optional[int]
    max_salary: Optional[int]
    remote_only: bool
    relocate: bool
    preferred_countries: List[str]
    years_of_experience: Optional[float]
    current_title: Optional[str]
    current_company: Optional[str]
    resume_text: Optional[str]
    skills: List[dict]
    
    class Config:
        from_attributes = True


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's profile"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not profile:
        # Create default profile
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    skills = [{"id": s.id, "name": s.name, "category": s.category, "years": s.years, "proficiency": s.proficiency} for s in profile.skills]
    
    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        first_name=profile.first_name,
        last_name=profile.last_name,
        location=profile.location,
        timezone=profile.timezone,
        desired_roles=profile.desired_roles or [],
        desired_industries=profile.desired_industries or [],
        min_salary=profile.min_salary,
        max_salary=profile.max_salary,
        remote_only=profile.remote_only or False,
        relocate=profile.relocate or False,
        preferred_countries=profile.preferred_countries or [],
        years_of_experience=profile.years_of_experience,
        current_title=profile.current_title,
        current_company=profile.current_company,
        resume_text=profile.resume_text,
        skills=skills,
    )


@router.patch("/me", response_model=ProfileResponse)
async def update_my_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user's profile"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    
    # Update fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    
    skills = [{"id": s.id, "name": s.name, "category": s.category, "years": s.years, "proficiency": s.proficiency} for s in profile.skills]
    
    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        first_name=profile.first_name,
        last_name=profile.last_name,
        location=profile.location,
        timezone=profile.timezone,
        desired_roles=profile.desired_roles or [],
        desired_industries=profile.desired_industries or [],
        min_salary=profile.min_salary,
        max_salary=profile.max_salary,
        remote_only=profile.remote_only or False,
        relocate=profile.relocate or False,
        preferred_countries=profile.preferred_countries or [],
        years_of_experience=profile.years_of_experience,
        current_title=profile.current_title,
        current_company=profile.current_company,
        resume_text=profile.resume_text,
        skills=skills,
    )


@router.post("/me/skills")
async def add_skill(
    skill_data: SkillInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a skill to user's profile"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    skill = Skill(
        profile_id=profile.id,
        name=skill_data.name,
        category=skill_data.category,
        years=skill_data.years,
        proficiency=skill_data.proficiency,
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    
    return {"id": skill.id, "name": skill.name, "status": "added"}


@router.delete("/me/skills/{skill_id}")
async def remove_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a skill from user's profile"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    skill = db.query(Skill).filter(Skill.id == skill_id, Skill.profile_id == profile.id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    db.delete(skill)
    db.commit()
    
    return {"status": "deleted", "skill_id": skill_id}


@router.post("/me/resume")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload resume (PDF/TXT)"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    # Read file content
    content = await file.read()
    text = content.decode('utf-8', errors='ignore')
    
    # Save resume text (in production, save to S3 and parse with AI)
    profile.resume_text = text
    db.commit()
    
    return {
        "status": "uploaded",
        "filename": file.filename,
        "size": len(content),
        "message": "Resume saved. AI parsing coming soon."
    }
