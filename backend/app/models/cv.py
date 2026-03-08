"""
CV/Resume Model
"""
from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class CV(Base):
    __tablename__ = "cvs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Personal Info
    full_name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    phone = Column(String(50))
    location = Column(String(200))
    linkedin_url = Column(String(300))
    portfolio_url = Column(String(300))
    
    # Professional Summary (AI-generated or manual)
    summary = Column(Text)
    
    # Experience (stored as JSON for flexibility)
    # Format: [{"company": "...", "role": "...", "start_date": "...", "end_date": "...", "description": "..."}]
    experience = Column(JSON, default=list)
    
    # Education (stored as JSON)
    # Format: [{"institution": "...", "degree": "...", "field": "...", "graduation_year": "..."}]
    education = Column(JSON, default=list)
    
    # Skills
    skills = Column(JSON, default=list)  # ["Python", "React", "AWS", ...]
    
    # Certifications (optional)
    certifications = Column(JSON, default=list)
    
    # Projects (optional)
    projects = Column(JSON, default=list)
    
    # Template selection
    template_id = Column(String(50), default="modern")  # modern, classic, minimal, creative
    
    # File storage
    file_url = Column(String(500))  # S3/cloud storage URL
    file_path = Column(String(500))  # Local path (for development)
    
    # AI-generated flag
    is_ai_generated = Column(Boolean, default=False)
    
    # Versioning
    version = Column(Integer, default=1)
    is_primary = Column(Boolean, default=False)  # User's main CV
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="cvs")
    applications = relationship("Application", back_populates="cv")


class CVTemplate(Base):
    __tablename__ = "cv_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)  # modern, classic, minimal, creative
    description = Column(Text)
    html_template = Column(Text, nullable=False)  # HTML/CSS template
    is_premium = Column(Boolean, default=False)  # Free vs Premium feature
    
    created_at = Column(DateTime, default=datetime.utcnow)
