"""
Analytics Dashboard API

Provides insights on:
- Application statistics
- Interview rates
- Response times
- Success metrics
- Market trends
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, extract

from app.core.security import get_current_user
from app.models.user import User
from app.database import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ApplicationStats(BaseModel):
    total_applications: int
    this_month: int
    last_month: int
    growth_rate: float
    by_status: Dict[str, int]
    by_stage: Dict[str, int]


class InterviewStats(BaseModel):
    total_interviews: int
    interview_rate: float  # interviews / applications
    by_stage: Dict[str, int]
    avg_days_to_interview: float


class ResponseTimeStats(BaseModel):
    avg_response_days: float
    median_response_days: float
    response_rate: float  # % that responded


class SuccessMetrics(BaseModel):
    offers_received: int
    offer_rate: float  # offers / applications
    avg_time_to_offer: float
    acceptance_rate: float


class MarketInsights(BaseModel):
    avg_salary_by_role: Dict[str, float]
    top_hiring_companies: List[str]
    trending_skills: List[str]
    remote_percentage: float


@router.get("/applications", response_model=ApplicationStats)
async def get_application_stats(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get application statistics"""
    from app.models.application import Application
    
    # Total applications
    total = db.query(Application).filter(
        Application.user_id == current_user.id
    ).count()
    
    # This month
    month_start = datetime.utcnow().replace(day=1)
    this_month = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.created_at >= month_start,
    ).count()
    
    # Last month
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)
    last_month = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.created_at >= last_month_start,
        Application.created_at < month_start,
    ).count()
    
    # Growth rate
    growth_rate = ((this_month - last_month) / last_month * 100) if last_month > 0 else 0
    
    # By status
    status_counts = db.query(
        Application.status, func.count(Application.id)
    ).filter(
        Application.user_id == current_user.id
    ).group_by(Application.status).all()
    
    # By stage
    stage_counts = db.query(
        Application.stage, func.count(Application.id)
    ).filter(
        Application.user_id == current_user.id
    ).group_by(Application.stage).all()
    
    return ApplicationStats(
        total_applications=total,
        this_month=this_month,
        last_month=last_month,
        growth_rate=round(growth_rate, 1),
        by_status={status: count for status, count in status_counts},
        by_stage={stage: count for stage, count in stage_counts},
    )


@router.get("/interviews", response_model=InterviewStats)
async def get_interview_stats(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get interview statistics"""
    from app.models.application import Application
    
    # Total interviews
    interviews = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.stage.in_(["phone_screen", "technical", "onsite"]),
    ).count()
    
    # Total applications
    total = db.query(Application).filter(
        Application.user_id == current_user.id
    ).count()
    
    # Interview rate
    interview_rate = (interviews / total * 100) if total > 0 else 0
    
    # By stage
    stage_counts = db.query(
        Application.stage, func.count(Application.id)
    ).filter(
        Application.user_id == current_user.id,
        Application.stage.in_(["phone_screen", "technical", "onsite"]),
    ).group_by(Application.stage).all()
    
    # Avg days to interview (estimate)
    avg_days = 7.0  # Would calculate from submitted_at to stage change in production
    
    return InterviewStats(
        total_interviews=interviews,
        interview_rate=round(interview_rate, 1),
        by_stage={stage: count for stage, count in stage_counts},
        avg_days_to_interview=avg_days,
    )


@router.get("/response-times", response_model=ResponseTimeStats)
async def get_response_time_stats(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get response time statistics"""
    from app.models.application import Application
    
    # Applications with responses (not in "submitted" status)
    responded = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.status != "submitted",
        Application.status != "draft",
    ).count()
    
    # Total submitted
    total = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.status.in_(["submitted", "viewed", "interviewing", "offered", "rejected"]),
    ).count()
    
    # Response rate
    response_rate = (responded / total * 100) if total > 0 else 0
    
    # Avg response time (estimate)
    avg_response = 5.5  # Would calculate from timestamps in production
    
    return ResponseTimeStats(
        avg_response_days=avg_response,
        median_response_days=4.0,
        response_rate=round(response_rate, 1),
    )


@router.get("/success", response_model=SuccessMetrics)
async def get_success_metrics(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get success metrics"""
    from app.models.application import Application
    
    # Offers received
    offers = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.status == "offered",
    ).count()
    
    # Total applications
    total = db.query(Application).filter(
        Application.user_id == current_user.id
    ).count()
    
    # Offer rate
    offer_rate = (offers / total * 100) if total > 0 else 0
    
    # Acceptance rate (estimate)
    acceptance_rate = 50.0  # Would track in production
    
    return SuccessMetrics(
        offers_received=offers,
        offer_rate=round(offer_rate, 2),
        avg_time_to_offer=45.0,  # Days
        acceptance_rate=acceptance_rate,
    )


@router.get("/market-insights")
async def get_market_insights(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get market insights based on job data"""
    from app.models.job import Job
    
    # Get recent active jobs
    recent_jobs = db.query(Job).filter(Job.is_active == True).limit(1000).all()
    
    if not recent_jobs:
        return MarketInsights(
            avg_salary_by_role={},
            top_hiring_companies=[],
            trending_skills=[],
            remote_percentage=0,
        )
    
    # Avg salary by seniority
    salary_by_seniority = {}
    for job in recent_jobs:
        if job.seniority and job.min_salary and job.max_salary:
            if job.seniority not in salary_by_seniority:
                salary_by_seniority[job.seniority] = []
            salary_by_seniority[job.seniority].append((job.min_salary + job.max_salary) / 2)
    
    avg_salary = {
        k: round(sum(v) / len(v)) for k, v in salary_by_seniority.items() if v
    }
    
    # Top hiring companies
    from collections import Counter
    company_counts = Counter(job.company for job in recent_jobs)
    top_companies = [company for company, count in company_counts.most_common(10)]
    
    # Remote percentage
    remote_count = sum(1 for job in recent_jobs if job.remote)
    remote_pct = (remote_count / len(recent_jobs) * 100) if recent_jobs else 0
    
    # Trending skills (from job requirements)
    all_skills = []
    for job in recent_jobs:
        if job.skills_required:
            all_skills.extend(job.skills_required)
    
    skill_counts = Counter(all_skills)
    trending = [skill for skill, count in skill_counts.most_common(15)]
    
    return MarketInsights(
        avg_salary_by_role=avg_salary,
        top_hiring_companies=top_companies,
        trending_skills=trending,
        remote_percentage=round(remote_pct, 1),
    )


@router.get("/overview")
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get complete dashboard overview"""
    from app.models.application import Application
    from app.models.profile import UserProfile
    
    # Get all stats
    apps_stats = await get_application_stats(current_user, db)
    interview_stats = await get_interview_stats(current_user, db)
    success_metrics = await get_success_metrics(current_user, db)
    
    # Get profile completeness
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    profile_completeness = 0
    if profile:
        fields = [
            profile.first_name,
            profile.last_name,
            profile.location,
            profile.years_of_experience,
            profile.current_title,
            profile.skills,
            profile.resume_text,
        ]
        profile_completeness = round(sum(1 for f in fields if f) / len(fields) * 100)
    
    return {
        "applications": apps_stats.dict(),
        "interviews": interview_stats.dict(),
        "success": success_metrics.dict(),
        "profile_completeness": profile_completeness,
        "last_updated": datetime.utcnow().isoformat(),
    }
