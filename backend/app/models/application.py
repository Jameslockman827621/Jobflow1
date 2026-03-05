from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Application(Base, TimestampMixin):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    
    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    
    # Application status
    status = Column(String, default="draft")  # draft, submitted, viewed, interviewing, offered, rejected, withdrawn
    stage = Column(String, default="not_started")  # not_started, applied, phone_screen, technical, onsite, offer
    
    # AI-generated content
    tailored_cv_url = Column(String)
    cover_letter = Column(Text)
    answers = Column(JSON, default=dict)  # Application-specific Q&A
    
    # Tracking
    submitted_at = Column(DateTime)
    last_follow_up = Column(DateTime)
    next_action = Column(DateTime)
    
    # Notes
    internal_notes = Column(Text)
    external_notes = Column(Text)  # From company/recruiter
    
    # Success tracking
    interview_count = Column(Integer, default=0)
    outcome = Column(String)  # hired, rejected, ghosted, withdrawn
    
    # Metadata
    applied_via = Column(String)  # "auto", "manual", "semi_auto"
    confidence_score = Column(Float)  # AI-predicted interview probability
