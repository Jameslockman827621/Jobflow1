"""
Search Cache Model

Caches job search results for users to avoid repeated API calls.
TTL-based expiration (default 24-48 hours).
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index, JSON, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from datetime import datetime, timedelta


class SearchCache(Base, TimestampMixin):
    """
    Cached job search results.
    
    Each user has cached search results that expire after TTL.
    Automatic refresh on access if expired.
    """
    __tablename__ = "search_cache"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Search parameters (for cache key)
    search_key = Column(String, nullable=False)  # Hash of search params
    search_params = Column(JSON, default=dict)  # Original search parameters
    
    # Results
    job_ids = Column(JSON, default=list)  # List of job IDs from search
    total_results = Column(Integer, default=0)
    
    # Cache metadata
    source = Column(String)  # "linkedin", "greenhouse", "lever", "combined"
    expires_at = Column(DateTime, nullable=False)
    is_valid = Column(Boolean, default=True)
    
    # Performance tracking
    search_duration_ms = Column(Integer)
    jobs_found = Column(Integer, default=0)
    jobs_cached = Column(Integer, default=0)
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'search_key', name='uix_user_search_key'),
        Index('idx_cache_expires', 'expires_at'),
        Index('idx_cache_valid', 'is_valid'),
    )
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return datetime.utcnow() > self.expires_at
    
    def should_refresh(self) -> bool:
        """Check if cache should be refreshed (within 2 hours of expiry)"""
        refresh_threshold = self.expires_at - timedelta(hours=2)
        return datetime.utcnow() > refresh_threshold
    
    @classmethod
    def create_cache_key(cls, params: dict) -> str:
        """
        Create a unique cache key from search parameters.
        
        Includes: roles, locations, remote, min_salary, companies
        Excludes: timestamps, user-specific metadata
        """
        import hashlib
        
        # Normalize params for consistent hashing
        key_params = {
            "roles": sorted(params.get("target_roles", [])),
            "locations": sorted(params.get("locations", [])),
            "remote": params.get("remote_only", False),
            "min_salary": params.get("min_salary"),
            "companies": sorted(params.get("target_companies", [])),
            "seniority": sorted(params.get("seniority_levels", [])),
        }
        
        # Create hash
        key_str = str(sorted(key_params.items()))
        return hashlib.md5(key_str.encode()).hexdigest()
    
    @classmethod
    def create_from_search(
        cls,
        user_id: int,
        params: dict,
        job_ids: list,
        source: str = "combined",
        ttl_hours: int = 24,
        search_duration_ms: int = 0,
    ) -> "SearchCache":
        """Create a new cache entry from search results"""
        return cls(
            user_id=user_id,
            search_key=cls.create_cache_key(params),
            search_params=params,
            job_ids=job_ids,
            total_results=len(job_ids),
            source=source,
            expires_at=datetime.utcnow() + timedelta(hours=ttl_hours),
            is_valid=True,
            search_duration_ms=search_duration_ms,
            jobs_found=len(job_ids),
            jobs_cached=len(job_ids),
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "search_key": self.search_key,
            "search_params": self.search_params,
            "job_count": len(self.job_ids) if self.job_ids else 0,
            "total_results": self.total_results,
            "source": self.source,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_valid": self.is_valid,
            "is_expired": self.is_expired(),
            "search_duration_ms": self.search_duration_ms,
        }
