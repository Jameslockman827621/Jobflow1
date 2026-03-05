from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Personal
    first_name = Column(String)
    last_name = Column(String)
    location = Column(String)  # e.g., "London, UK"
    timezone = Column(String, default="UTC")
    
    # Job preferences
    desired_roles = Column(JSON, default=list)  # ["Software Engineer", "Senior Developer"]
    desired_industries = Column(JSON, default=list)
    min_salary = Column(Integer)  # Annual, in local currency
    max_salary = Column(Integer)
    remote_only = Column(Boolean, default=False)
    relocate = Column(Boolean, default=False)
    preferred_countries = Column(JSON, default=["UK", "US"])
    
    # Experience
    years_of_experience = Column(Float)
    current_title = Column(String)
    current_company = Column(String)
    
    # Resume
    resume_text = Column(Text)  # Parsed resume content
    resume_url = Column(String)  # S3 or local path
    
    # Relationships
    user = relationship("User", back_populates="profile")
    skills = relationship("Skill", back_populates="profile", cascade="all, delete-orphan")


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String)  # e.g., "Programming", "Design", "Management"
    years = Column(Float)
    proficiency = Column(String)  # "beginner", "intermediate", "advanced", "expert"
    
    # Relationships
    profile = relationship("UserProfile", back_populates="skills")
