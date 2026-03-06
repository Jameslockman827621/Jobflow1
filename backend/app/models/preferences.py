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
    
    Mapped to scraper capabilities:
    - LinkedIn: keywords, location, date_posted, job_type, remote
    - Indeed: query, location, country, remote, job_type, level, from_days
    """
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    
    # === ROLE & SENIORITY (Both scrapers) ===
    target_roles = Column(ARRAY(String), default=list)  # ["Software Engineer", "Senior Developer"]
    seniority_levels = Column(ARRAY(String), default=list)  # ["entry", "mid", "senior", "lead", "director", "executive"]
    
    # === LOCATION & REMOTE (Both scrapers) ===
    locations = Column(ARRAY(String), default=list)  # ["London", "New York", "Remote"]
    countries = Column(ARRAY(String), default=list)  # ["uk", "us", "ca", "au", "de", "fr"] - Indeed country codes
    remote_preference = Column(String, default="any")  # "remote_only", "hybrid_ok", "onsite_only", "any"
    
    # === JOB TYPE & TIMING (Both scrapers) ===
    employment_types = Column(ARRAY(String), default=list)  # ["fulltime", "parttime", "contract", "internship"]
    date_posted = Column(String, default="month")  # "day", "week", "month", "any" (LinkedIn) / 1-30 days (Indeed)
    
    # === COMPENSATION (Filtering only) ===
    min_salary = Column(Integer)  # Minimum acceptable salary
    salary_currency = Column(String, default="GBP")
    salary_period = Column(String, default="YEAR")  # YEAR, HOUR, etc.
    
    # === COMPANY PREFERENCES (Greenhouse/Lever direct) ===
    target_companies = Column(ARRAY(String), default=list)  # ["Stripe", "Figma", "Airbnb"]
    company_sizes = Column(ARRAY(String), default=list)  # ["startup", "mid", "enterprise"]
    exclude_companies = Column(ARRAY(String), default=list)  # Companies to exclude
    
    # === INDUSTRY & DEPARTMENT (LinkedIn job function) ===
    industries = Column(ARRAY(String), default=list)  # ["Fintech", "SaaS", "E-commerce"]
    departments = Column(ARRAY(String), default=list)  # ["Engineering", "Product", "Data"]
    
    # === SKILLS (Matching, not search) ===
    required_skills = Column(ARRAY(String), default=list)  # Must-have skills
    nice_to_have_skills = Column(ARRAY(String), default=list)  # Bonus skills
    
    # === SEARCH METADATA ===
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
            # Role & Seniority
            "target_roles": self.target_roles or [],
            "seniority_levels": self.seniority_levels or [],
            # Location & Remote
            "locations": self.locations or [],
            "countries": self.countries or [],
            "remote_preference": self.remote_preference or "any",
            # Job Type & Timing
            "employment_types": self.employment_types or [],
            "date_posted": self.date_posted or "month",
            # Compensation
            "min_salary": self.min_salary,
            "salary_currency": self.salary_currency,
            "salary_period": self.salary_period,
            # Company
            "target_companies": self.target_companies or [],
            "company_sizes": self.company_sizes or [],
            "exclude_companies": self.exclude_companies or [],
            # Industry
            "industries": self.industries or [],
            "departments": self.departments or [],
            # Skills
            "required_skills": self.required_skills or [],
            "nice_to_have_skills": self.nice_to_have_skills or [],
            # Metadata
            "is_active": self.is_active,
            "last_search_run": self.last_search_run.isoformat() if self.last_search_run else None,
            "search_frequency_hours": self.search_frequency_hours,
        }
    
    @classmethod
    def from_dict(cls, data: dict, user_id: int) -> "UserPreferences":
        """Create from dictionary (API request)"""
        return cls(
            user_id=user_id,
            # Role & Seniority
            target_roles=data.get("target_roles", []),
            seniority_levels=data.get("seniority_levels", []),
            # Location & Remote
            locations=data.get("locations", []),
            countries=data.get("countries", []),
            remote_preference=data.get("remote_preference", "any"),
            # Job Type & Timing
            employment_types=data.get("employment_types", []),
            date_posted=data.get("date_posted", "month"),
            # Compensation
            min_salary=data.get("min_salary"),
            salary_currency=data.get("salary_currency", "GBP"),
            salary_period=data.get("salary_period", "YEAR"),
            # Company
            target_companies=data.get("target_companies", []),
            company_sizes=data.get("company_sizes", []),
            exclude_companies=data.get("exclude_companies", []),
            # Industry
            industries=data.get("industries", []),
            departments=data.get("departments", []),
            # Skills
            required_skills=data.get("required_skills", []),
            nice_to_have_skills=data.get("nice_to_have_skills", []),
            # Metadata
            search_frequency_hours=data.get("search_frequency_hours", 24),
        )
