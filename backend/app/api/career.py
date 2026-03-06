"""
Career Pathing API

Endpoints:
- GET /career/analysis - Get personalized career analysis
- GET /career/paths - Browse career paths by role
- GET /career/salary - Get salary data by role/level
- POST /career/goals - Set career goals
- GET /career/goals - Get user's career goals
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict

from app.core.security import get_current_user
from app.models.user import User
from app.database import SessionLocal
from app.services.career_pathing import career_pathing
from app.services.matching import JobMatcher

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CareerAnalysisResponse(BaseModel):
    current_level: str
    career_path: dict
    skill_gaps: list
    recommendations: list
    salary_trajectory: list
    next_milestone: dict


class CareerGoal(BaseModel):
    target_role: str
    target_company: Optional[str] = None
    target_salary: Optional[int] = None
    timeline_months: int
    notes: Optional[str] = ""


@router.get("/analysis", response_model=CareerAnalysisResponse)
async def get_career_analysis(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get personalized career analysis based on user's profile"""
    from app.models.profile import UserProfile
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Please complete your profile first.")
    
    # Convert profile to dict for analysis
    profile_dict = {
        "current_title": profile.current_title,
        "years_of_experience": profile.years_of_experience,
        "skills": [{"name": s.name} for s in profile.skills],
        "location": profile.location,
        "min_salary": profile.min_salary,
        "max_salary": profile.max_salary,
    }
    
    analysis = career_pathing.analyze_profile(profile_dict)
    
    return CareerAnalysisResponse(**analysis)


@router.get("/paths")
async def get_career_paths(
    role: Optional[str] = Query(None, description="Filter by role"),
):
    """Browse available career paths"""
    paths = career_pathing.CAREER_PATHS
    
    if role:
        # Filter paths by role
        role_lower = role.lower()
        filtered = {
            k: v for k, v in paths.items() 
            if role_lower in k or role_lower in " ".join([p["title"] for p in v.get("progression", [])])
        }
        return {"paths": filtered}
    
    return {"paths": paths}


@router.get("/salary")
async def get_salary_data(
    role: str = Query(..., description="Role to get salary data for"),
    location: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
):
    """Get salary data for a specific role"""
    career_path = career_pathing._find_matching_career_path(role)
    
    progression = career_path.get("progression", [])
    
    # Filter by level if provided
    if level:
        progression = [p for p in progression if level.lower() in p["title"].lower()]
    
    return {
        "role": role,
        "location": location or "US (national average)",
        "salary_data": progression,
        "note": "Salaries are estimates based on market data. Actual salaries vary by company, location, and individual.",
    }


@router.post("/goals")
async def set_career_goals(
    goal: CareerGoal,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Set career goals"""
    from app.models.profile import UserProfile
    from sqlalchemy import JSON
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    
    # Store goals in a JSON field (would add proper model in production)
    if not hasattr(profile, "career_goals"):
        profile.desired_roles = [goal.target_role]
    
    if goal.target_salary:
        profile.max_salary = goal.target_salary
    
    db.commit()
    
    return {
        "status": "saved",
        "goal": goal.dict(),
        "message": f"Goal set: {goal.target_role} in {goal.timeline_months} months",
    }


@router.get("/goals")
async def get_career_goals(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get user's career goals"""
    from app.models.profile import UserProfile
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not profile:
        return {"goals": None, "message": "No profile found. Set your goals to get started."}
    
    return {
        "goals": {
            "target_roles": profile.desired_roles,
            "target_salary": profile.max_salary,
            "current_title": profile.current_title,
            "current_company": profile.current_company,
        }
    }


@router.get("/recommendations")
async def get_job_recommendations(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get job recommendations based on career goals"""
    from app.models.job import Job
    from app.models.profile import UserProfile
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        return {"jobs": [], "message": "Complete your profile first"}
    
    # Get jobs that match career progression
    matcher = JobMatcher(db)
    jobs = db.query(Job).filter(Job.is_active == True).limit(20).all()
    
    # Score and sort
    scored = []
    for job in jobs:
        score = matcher.calculate_match_score(profile, job)
        if score >= 60:
            scored.append({
                "job": {
                    "id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "salary_min": job.min_salary,
                    "salary_max": job.max_salary,
                    "seniority": job.seniority,
                },
                "match_score": score,
                "career_fit": "promotion" if job.seniority in ["senior", "lead"] else "lateral",
            })
    
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    
    return {"jobs": scored[:10]}
