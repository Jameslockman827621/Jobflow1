from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from datetime import datetime


class CompanyReview(Base, TimestampMixin):
    """User reviews of companies"""
    __tablename__ = "company_reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Company info
    company_name = Column(String, nullable=False, index=True)
    company_url = Column(String)
    
    # Ratings (1-5)
    overall_rating = Column(Float, nullable=False)
    work_life_balance = Column(Float)
    culture_rating = Column(Float)
    compensation_rating = Column(Float)
    career_opportunities = Column(Float)
    management_rating = Column(Float)
    
    # Review content
    title = Column(String, nullable=False)
    pros = Column(Text)
    cons = Column(Text)
    advice_to_management = Column(Text)
    
    # Job-specific
    job_title = Column(String)
    department = Column(String)
    employment_status = Column(String)  # current, former, candidate
    interview_experience = Column(String)  # positive, neutral, negative
    interview_difficulty = Column(Integer)  # 1-5
    
    # Metadata
    location = Column(String)
    salary_shared = Column(Integer)
    is_anonymous = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)  # Verified employee
    
    # Engagement
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_company_name', 'company_name'),
        Index('idx_overall_rating', 'overall_rating'),
    )


class InterviewReview(Base, TimestampMixin):
    """Specific interview experience reviews"""
    __tablename__ = "interview_reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Company info
    company_name = Column(String, nullable=False, index=True)
    
    # Interview details
    job_title = Column(String, nullable=False)
    interview_type = Column(String)  # phone, technical, onsite, etc.
    
    # Experience
    experience_rating = Column(Integer)  # 1-5
    difficulty_rating = Column(Integer)  # 1-5
    process_duration_days = Column(Integer)
    
    # Questions
    questions_asked = Column(Text)  # JSON array of questions
    interview_questions_count = Column(Integer)
    
    # Outcome
    received_offer = Column(Boolean)
    
    # Content
    description = Column(Text)
    tips = Column(Text)
    
    # Metadata
    location = Column(String)
    date_interviewed = Column(DateTime)
    is_anonymous = Column(Boolean, default=False)
    
    # Engagement
    helpful_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User")
