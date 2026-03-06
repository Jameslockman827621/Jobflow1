"""
Company Reviews API

Glassdoor-style reviews for companies:
- Rate companies
- Read reviews from other job seekers
- Interview experiences
- Salary information

Endpoints:
- POST /reviews/company - Create/update company review
- GET /reviews/company/{name} - Get reviews for a company
- GET /reviews/my - Get user's reviews
- POST /reviews/interview - Submit interview experience
- GET /reviews/companies - Browse companies with reviews
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from sqlalchemy import func

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


class CompanyReviewCreate(BaseModel):
    company_name: str
    company_url: Optional[str] = None
    overall_rating: float = Field(..., ge=1, le=5)
    work_life_balance: Optional[float] = Field(None, ge=1, le=5)
    culture_rating: Optional[float] = Field(None, ge=1, le=5)
    compensation_rating: Optional[float] = Field(None, ge=1, le=5)
    career_opportunities: Optional[float] = Field(None, ge=1, le=5)
    management_rating: Optional[float] = Field(None, ge=1, le=5)
    title: str
    pros: str
    cons: str
    advice_to_management: Optional[str] = ""
    job_title: Optional[str] = ""
    department: Optional[str] = ""
    employment_status: str = "candidate"
    interview_experience: Optional[str] = None
    interview_difficulty: Optional[int] = Field(None, ge=1, le=5)
    location: Optional[str] = ""
    salary_shared: Optional[int] = None
    is_anonymous: bool = False


class CompanyReviewResponse(BaseModel):
    id: int
    company_name: str
    overall_rating: float
    work_life_balance: Optional[float]
    culture_rating: Optional[float]
    compensation_rating: Optional[float]
    career_opportunities: Optional[float]
    management_rating: Optional[float]
    title: str
    pros: str
    cons: str
    job_title: Optional[str]
    employment_status: str
    created_at: str
    helpful_count: int
    is_anonymous: bool
    
    class Config:
        from_attributes = True


class InterviewReviewCreate(BaseModel):
    company_name: str
    job_title: str
    interview_type: Optional[str] = "onsite"
    experience_rating: int = Field(..., ge=1, le=5)
    difficulty_rating: int = Field(..., ge=1, le=5)
    process_duration_days: Optional[int] = None
    questions_asked: Optional[str] = ""
    received_offer: Optional[bool] = None
    description: str
    tips: Optional[str] = ""
    location: Optional[str] = ""
    is_anonymous: bool = False


@router.post("/company", response_model=CompanyReviewResponse)
async def create_company_review(
    review: CompanyReviewCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Create or update a company review"""
    from app.models.review import CompanyReview
    
    # Check if user already reviewed this company
    existing = db.query(CompanyReview).filter(
        CompanyReview.user_id == current_user.id,
        CompanyReview.company_name == review.company_name,
    ).first()
    
    if existing:
        # Update existing review
        for field, value in review.dict(exclude_unset=True).items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return CompanyReviewResponse(
            id=existing.id,
            company_name=existing.company_name,
            overall_rating=existing.overall_rating,
            work_life_balance=existing.work_life_balance,
            culture_rating=existing.culture_rating,
            compensation_rating=existing.compensation_rating,
            career_opportunities=existing.career_opportunities,
            management_rating=existing.management_rating,
            title=existing.title,
            pros=existing.pros,
            cons=existing.cons,
            job_title=existing.job_title,
            employment_status=existing.employment_status,
            created_at=existing.created_at.isoformat(),
            helpful_count=existing.helpful_count,
            is_anonymous=existing.is_anonymous,
        )
    
    # Create new review
    new_review = CompanyReview(
        user_id=current_user.id,
        **review.dict(),
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    
    return CompanyReviewResponse(
        id=new_review.id,
        company_name=new_review.company_name,
        overall_rating=new_review.overall_rating,
        work_life_balance=new_review.work_life_balance,
        culture_rating=new_review.culture_rating,
        compensation_rating=new_review.compensation_rating,
        career_opportunities=new_review.career_opportunities,
        management_rating=new_review.management_rating,
        title=new_review.title,
        pros=new_review.pros,
        cons=new_review.cons,
        job_title=new_review.job_title,
        employment_status=new_review.employment_status,
        created_at=new_review.created_at.isoformat(),
        helpful_count=new_review.helpful_count,
        is_anonymous=new_review.is_anonymous,
    )


@router.get("/company/{company_name}")
async def get_company_reviews(
    company_name: str,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db = Depends(get_db),
):
    """Get all reviews for a company"""
    from app.models.review import CompanyReview
    
    # Get reviews
    reviews = db.query(CompanyReview).filter(
        CompanyReview.company_name.ilike(f"%{company_name}%")
    ).order_by(CompanyReview.created_at.desc()).offset(offset).limit(limit).all()
    
    # Calculate averages
    avg_ratings = db.query(
        avg(CompanyReview.overall_rating),
        avg(CompanyReview.work_life_balance),
        avg(CompanyReview.culture_rating),
        avg(CompanyReview.compensation_rating),
        avg(CompanyReview.career_opportunities),
        avg(CompanyReview.management_rating),
    ).filter(
        CompanyReview.company_name.ilike(f"%{company_name}%")
    ).first()
    
    total = db.query(CompanyReview).filter(
        CompanyReview.company_name.ilike(f"%{company_name}%")
    ).count()
    
    return {
        "company_name": company_name,
        "total_reviews": total,
        "average_ratings": {
            "overall": round(avg_ratings[0] or 0, 1),
            "work_life_balance": round(avg_ratings[1] or 0, 1),
            "culture": round(avg_ratings[2] or 0, 1),
            "compensation": round(avg_ratings[3] or 0, 1),
            "career_opportunities": round(avg_ratings[4] or 0, 1),
            "management": round(avg_ratings[5] or 0, 1),
        },
        "reviews": [
            {
                "id": r.id,
                "overall_rating": r.overall_rating,
                "title": r.title,
                "pros": r.pros,
                "cons": r.cons,
                "job_title": r.job_title,
                "employment_status": r.employment_status,
                "created_at": r.created_at.isoformat(),
                "helpful_count": r.helpful_count,
                "is_anonymous": r.is_anonymous,
            }
            for r in reviews
        ],
    }


@router.get("/my")
async def get_my_reviews(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get current user's reviews"""
    from app.models.review import CompanyReview
    
    reviews = db.query(CompanyReview).filter(
        CompanyReview.user_id == current_user.id
    ).order_by(CompanyReview.created_at.desc()).all()
    
    return {
        "reviews": [
            {
                "id": r.id,
                "company_name": r.company_name,
                "overall_rating": r.overall_rating,
                "title": r.title,
                "created_at": r.created_at.isoformat(),
            }
            for r in reviews
        ]
    }


@router.post("/interview")
async def create_interview_review(
    review: InterviewReviewCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Submit interview experience review"""
    from app.models.review import InterviewReview
    
    new_review = InterviewReview(
        user_id=current_user.id,
        **review.dict(),
    )
    db.add(new_review)
    db.commit()
    
    return {
        "status": "created",
        "message": "Interview review submitted! Thank you for sharing your experience.",
    }


@router.get("/companies")
async def get_companies_with_reviews(
    limit: int = Query(20, le=100),
    db = Depends(get_db),
):
    """Get companies sorted by review count/rating"""
    from app.models.review import CompanyReview
    
    companies = db.query(
        CompanyReview.company_name,
        func.count(CompanyReview.id).label("review_count"),
        avg(CompanyReview.overall_rating).label("avg_rating"),
    ).group_by(CompanyReview.company_name).order_by(
        func.count(CompanyReview.id).desc()
    ).limit(limit).all()
    
    return {
        "companies": [
            {
                "name": c.company_name,
                "review_count": c.review_count,
                "avg_rating": round(c.avg_rating or 0, 1),
            }
            for c in companies
        ]
    }


@router.get("/interview/{company_name}")
async def get_interview_reviews(
    company_name: str,
    limit: int = Query(20, le=100),
    db = Depends(get_db),
):
    """Get interview reviews for a company"""
    from app.models.review import InterviewReview
    
    reviews = db.query(InterviewReview).filter(
        InterviewReview.company_name.ilike(f"%{company_name}%")
    ).order_by(InterviewReview.created_at.desc()).limit(limit).all()
    
    # Calculate averages
    avg_stats = db.query(
        avg(InterviewReview.experience_rating),
        avg(InterviewReview.difficulty_rating),
        avg(InterviewReview.process_duration_days),
    ).filter(
        InterviewReview.company_name.ilike(f"%{company_name}%")
    ).first()
    
    total = db.query(InterviewReview).filter(
        InterviewReview.company_name.ilike(f"%{company_name}%")
    ).count()
    
    return {
        "company_name": company_name,
        "total_interviews": total,
        "averages": {
            "experience_rating": round(avg_stats[0] or 0, 1),
            "difficulty_rating": round(avg_stats[1] or 0, 1),
            "process_duration_days": round(avg_stats[2] or 0, 1),
        },
        "reviews": [
            {
                "id": r.id,
                "job_title": r.job_title,
                "interview_type": r.interview_type,
                "experience_rating": r.experience_rating,
                "difficulty_rating": r.difficulty_rating,
                "description": r.description,
                "tips": r.tips,
                "received_offer": r.received_offer,
                "created_at": r.created_at.isoformat(),
            }
            for r in reviews
        ],
    }
