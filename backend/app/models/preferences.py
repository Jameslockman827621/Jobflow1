"""
User Job Preferences Model

Stores what each user is looking for in a job.
Used for on-demand job searching and matching.
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index, JSON, ARRAY
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class UserPreferences(Base, TimestampMixin):
    """
    User's job search preferences.
    
    Populated during onboarding, updated by user anytime.
    Used to run targeted job searches on-demand.
    """
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    
    # Role/Title preferences
    target_roles = Column(ARRAY(String), default=list)  # ["Software Engineer", "Senior Developer"]
    seniority_levels = Column(ARRAY(String), default=list)  # ["mid", "senior", "lead"]
    
    # Location preferences
    locations = Column(ARRAY(String), default=list)  # ["London, UK", "Remote"]
    remote_only = Column(Boolean, default=False)
    hybrid_ok = Column(Boolean, default=True)
    relocate = Column(Boolean, default=False)
    
    # Compensation
    min_salary = Column(Integer)  # Minimum acceptable salary
    salary_currency = Column(String, default="GBP")
    salary_period = Column(String, default="YEAR")  # YEAR, HOUR, etc.
    
    # Company preferences
    target_companies = Column(ARRAY(String), default=list)  # ["Stripe", "Figma", "Airbnb"]
    company_sizes = Column(ARRAY(String), default=list)  # ["startup", "mid", "enterprise"]
    exclude_companies = Column(ARRAY(String), default=list)  # Companies to exclude
    
    # Industry/Department
    industries = Column(ARRAY(String), default=list)  # ["Fintech", "SaaS", "E-commerce"]
    departments = Column(ARRAY(String), default=list)  # ["Engineering", "Product", "Data"]
    
    # Skills
    required_skills = Column(ARRAY(String), default=list)  # Must-have skills
    nice_to_have_skills = Column(ARRAY(String), default=list)  # Bonus skills
    
    # Job type
    employment_types = Column(ARRAY(String), default=list)  # ["FULL_TIME", "CONTRACT"]
    
    # Search metadata
    is_active = Column(Boolean, default=True)
    last_search_run = Column(DateTime)
    search_frequency_hours = Column(Integer, default=24)  # How often to refresh
    
    # Relationship
    user = relationship("User", back_populates="preferences", uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_preferences_user', 'user_id'),
        Index('idx_preferences_active', 'is_active'),
    )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "target_roles": self.target_roles or [],
            "seniority_levels": self.seniority_levels or [],
            "locations": self.locations or [],
            "remote_only": self.remote_only,
            "hybrid_ok": self.hybrid_ok,
            "relocate": self.relocate,
            "min_salary": self.min_salary,
            "salary_currency": self.salary_currency,
            "salary_period": self.salary_period,
            "target_companies": self.target_companies or [],
            "company_sizes": self.company_sizes or [],
            "exclude_companies": self.exclude_companies or [],
            "industries": self.industries or [],
            "departments": self.departments or [],
            "required_skills": self.required_skills or [],
            "nice_to_have_skills": self.nice_to_have_skills or [],
            "employment_types": self.employment_types or [],
            "is_active": self.is_active,
            "last_search_run": self.last_search_run.isoformat() if self.last_search_run else None,
            "search_frequency_hours": self.search_frequency_hours,
        }
    
    @classmethod
    def from_dict(cls, data: dict, user_id: int) -> "UserPreferences":
        """Create from dictionary (API request)"""
        return cls(
            user_id=user_id,
            target_roles=data.get("target_roles", []),
            seniority_levels=data.get("seniority_levels", []),
            locations=data.get("locations", []),
            remote_only=data.get("remote_only", False),
            hybrid_ok=data.get("hybrid_ok", True),
            relocate=data.get("relocate", False),
            min_salary=data.get("min_salary"),
            salary_currency=data.get("salary_currency", "GBP"),
            salary_period=data.get("salary_period", "YEAR"),
            target_companies=data.get("target_companies", []),
            company_sizes=data.get("company_sizes", []),
            exclude_companies=data.get("exclude_companies", []),
            industries=data.get("industries", []),
            departments=data.get("departments", []),
            required_skills=data.get("required_skills", []),
            nice_to_have_skills=data.get("nice_to_have_skills", []),
            employment_types=data.get("employment_types", []),
            search_frequency_hours=data.get("search_frequency_hours", 24),
        )
