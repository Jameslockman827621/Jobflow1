from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class JobSource(Base, TimestampMixin):
    """Job aggregation sources (Greenhouse, Lever, etc.)"""
    __tablename__ = "job_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # "greenhouse", "lever", "google_jobs"
    base_url = Column(String)
    is_active = Column(Boolean, default=True)
    scrape_interval_hours = Column(Integer, default=24)
    last_scraped = Column(DateTime)
    
    jobs = relationship("Job", back_populates="source")


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Source tracking
    source_id = Column(Integer, ForeignKey("job_sources.id"), nullable=False)
    external_id = Column(String, index=True)  # ID from source
    external_url = Column(String, nullable=False)
    
    # Job details
    title = Column(String, nullable=False, index=True)
    company = Column(String, nullable=False, index=True)
    location = Column(String)
    remote = Column(Boolean, default=False)
    hybrid = Column(Boolean, default=False)
    
    # Compensation
    min_salary = Column(Integer)
    max_salary = Column(Integer)
    salary_currency = Column(String, default="USD")
    salary_period = Column(String, default="YEAR")  # YEAR, HOUR, etc.
    
    # Content
    description = Column(Text)
    requirements = Column(JSON, default=list)
    benefits = Column(JSON, default=list)
    
    # Metadata
    department = Column(String)
    seniority = Column(String)  # "entry", "mid", "senior", "lead", "executive"
    employment_type = Column(String, default="FULL_TIME")
    experience_years_min = Column(Float)
    experience_years_max = Column(Float)
    
    # Skills extracted from description
    skills_required = Column(JSON, default=list)
    
    # Matching
    match_score = Column(Float)  # Calculated per user
    is_active = Column(Boolean, default=True)
    
    # Scraping metadata
    scraped_at = Column(DateTime)
    posted_date = Column(DateTime)
    
    # Relationships
    source = relationship("JobSource", back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        # Performance indexes
        Index('idx_job_location', 'location'),
        Index('idx_job_seniority', 'seniority'),
        Index('idx_job_active', 'is_active'),
        Index('idx_job_company', 'company'),
        Index('idx_job_title', 'title'),
        
        # Unique constraint: source_id + external_id (prevents same-source duplicates)
        Index('uix_job_source_external', 'source_id', 'external_id', unique=True),
        
        # Index for URL-based deduplication (cross-source)
        Index('idx_job_external_url', 'external_url'),
    )
