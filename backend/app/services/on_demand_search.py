"""
On-Demand Job Search Service

Runs targeted job searches based on user preferences.
Delegates to JobAggregator for fan-out across all sources (ATS providers,
job boards, remote boards, Google Jobs, and direct career pages).
"""

import asyncio
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.job import Job, JobSource
from app.models.preferences import UserPreferences
from app.models.search_cache import SearchCache
from app.core.config import settings
from app.services.job_aggregator import JobAggregator, get_aggregator


class OnDemandSearchService:
    """
    Runs job searches on-demand based on user preferences.

    Flow:
    1. Check cache (if valid, return cached results)
    2. If expired/missing, delegate to JobAggregator for fan-out across all sources
    3. Save deduplicated results to DB
    4. Cache results
    5. Return fresh jobs
    """

    def __init__(self, db: Session):
        self.db = db
        self.aggregator: JobAggregator = get_aggregator()
    
    async def search_for_user(
        self,
        user_id: int,
        preferences: Optional[UserPreferences] = None,
        force_refresh: bool = False,
    ) -> Dict:
        """
        Search jobs for a specific user.
        
        Args:
            user_id: User ID
            preferences: User preferences (will fetch if not provided)
            force_refresh: Skip cache and run fresh search
        
        Returns:
            Dict with jobs, metadata, and cache info
        """
        start_time = time.time()
        
        # Fetch preferences if not provided
        if not preferences:
            preferences = self.db.query(UserPreferences).filter_by(
                user_id=user_id,
                is_active=True
            ).first()
            
            if not preferences:
                return {
                    "status": "error",
                    "message": "User preferences not found",
                    "jobs": [],
                    "total": 0
                }
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached = self._get_cached_search(user_id, preferences)
            if cached and not cached.is_expired():
                jobs = self._fetch_cached_jobs(cached)
                return {
                    "status": "cached",
                    "message": "Results from cache",
                    "jobs": jobs,
                    "total": len(jobs),
                    "cache": cached.to_dict(),
                    "search_duration_ms": 0
                }
        
        # Run fresh search via the aggregator
        search_start = time.time()
        jobs, sources_used, sources_failed = await self._run_searches(preferences)
        search_duration_ms = int((time.time() - search_start) * 1000)

        # When the aggregator returns no jobs, be honest — don't seed fake demo jobs.
        # The aggregator already runs runtime ATS discovery for any target companies,
        # so an empty result means the user hasn't configured target companies/roles
        # that match any current openings. Prompt them to broaden their search.
        if not jobs:
            total_duration_ms = int((time.time() - start_time) * 1000)
            return {
                "status": "no_results",
                "message": (
                    "No live jobs found for your search. Try adding target companies "
                    "(Settings → Preferences) or broadening your roles/locations. "
                    "We can apply to any company on Greenhouse, Lever, Ashby, Workable, "
                    "or Workday — even ones not in our curated list."
                ),
                "jobs": [],
                "total": 0,
                "search_duration_ms": search_duration_ms,
                "sources_used": sources_used or {},
                "sources_failed": sources_failed,
            }

        # Aggregator already deduplicated and filtered; collect source stats before save
        sources_used_pre = sources_used or self._get_sources_used(jobs)

        # Save jobs to database
        job_ids = self._save_jobs(jobs)

        # Update cache
        cache = self._update_cache(
            user_id=user_id,
            preferences=preferences,
            job_ids=job_ids,
            search_duration_ms=search_duration_ms
        )

        # Fetch full job objects
        job_objects = self._fetch_jobs_by_ids(job_ids)

        total_duration_ms = int((time.time() - start_time) * 1000)

        return {
            "status": "fresh",
            "message": f"Fresh search completed in {total_duration_ms}ms across {len(sources_used_pre)} sources",
            "jobs": job_objects,
            "total": len(job_objects),
            "cache": cache.to_dict(),
            "search_duration_ms": search_duration_ms,
            "sources_used": sources_used_pre,
            "sources_failed": sources_failed,
        }
    
    def _get_cached_search(self, user_id: int, preferences: UserPreferences) -> Optional[SearchCache]:
        """Get cached search results if available"""
        cache_key = SearchCache.create_cache_key(preferences.to_dict())
        
        cache = self.db.query(SearchCache).filter_by(
            user_id=user_id,
            search_key=cache_key,
            is_valid=True
        ).first()
        
        return cache
    
    def _fetch_cached_jobs(self, cache: SearchCache) -> List[Dict]:
        """Fetch jobs from cache"""
        if not cache.job_ids:
            return []
        
        jobs = self.db.query(Job).filter(
            Job.id.in_(cache.job_ids),
            Job.is_active == True
        ).all()
        
        return [self._job_to_dict(job) for job in jobs]
    
    async def _run_searches(self, preferences: UserPreferences) -> Tuple[List[Dict], Dict, List[str]]:
        """
        Delegate to JobAggregator which fans out across all sources in parallel.

        Returns:
            (jobs, sources_used, sources_failed)
        """
        # Build a single keyword query from target roles
        keywords = ""
        if preferences.target_roles:
            # Aggregator searches one keyword at a time; combine top roles
            keywords = " ".join(preferences.target_roles[:2])

        # Pick primary location
        location = None
        if preferences.locations:
            location = preferences.locations[0]

        # Remote filter
        remote_only = preferences.remote_preference in ("remote_only",)

        # Employment types — aggregator expects values like "fulltime"
        employment_types = preferences.employment_types or []

        # Seniority levels
        seniority_levels = preferences.seniority_levels or []

        result = await self.aggregator.search(
            keywords=keywords,
            location=location,
            target_companies=preferences.target_companies or [],
            remote_only=remote_only,
            employment_types=employment_types,
            seniority_levels=seniority_levels,
            max_results=200,
            max_per_source=50,
        )
        return result["jobs"], result.get("sources_used", {}), result.get("sources_failed", [])

    def _fallback_job_ids_from_db(self, preferences: UserPreferences) -> List[int]:
        """Return DB jobs matching roles. No longer seeds fake demo jobs —
        the search must return real results or honestly report no matches."""
        q = self.db.query(Job).filter(Job.is_active == True)
        roles = [r.strip() for r in (preferences.target_roles or []) if r.strip()]
        if roles:
            title_conds = [Job.title.ilike(f"%{r}%") for r in roles[:6]]
            q = q.filter(or_(*title_conds))

        rows = q.order_by(Job.posted_date.desc().nullslast()).limit(50).all()
        if not rows:
            rows = (
                self.db.query(Job)
                .filter(Job.is_active == True)
                .order_by(Job.posted_date.desc().nullslast())
                .limit(50)
                .all()
            )
        return [j.id for j in rows]

    def _save_jobs(self, jobs: List[Dict]) -> List[int]:
        """
        Save jobs to database and return IDs.
        
        Uses upsert (merge) to avoid duplicates.
        """
        job_ids = []
        
        # Get or create job sources — include every source the aggregator may emit
        source_names = [
            "linkedin", "indeed", "greenhouse", "lever", "ashby", "workable", "workday",
            "otta", "wellfound", "builtin", "remoteok", "weworkremotely",
            "remotive", "himalayas", "google_jobs", "career_page", "curated",
        ]
        sources = {}
        for source_name in source_names:
            source = self.db.query(JobSource).filter_by(name=source_name).first()
            if not source:
                source = JobSource(
                    name=source_name,
                    base_url=f"https://{source_name}.com",
                    is_active=True
                )
                self.db.add(source)
                self.db.commit()
                self.db.refresh(source)
            sources[source_name] = source

        default_source = sources.get("greenhouse") or next(iter(sources.values()))

        for job_data in jobs:
            source_name = job_data.pop("_source", "unknown")
            src = sources.get(source_name) or default_source
            source_id = src.id

            # Skip jobs missing required fields (DB has NOT NULL on title/company/external_url)
            if not job_data.get("title") or not job_data.get("company") or not job_data.get("external_url"):
                continue

            # Enrich the job with structured fields extracted from the description
            try:
                from app.services.job_enricher import enrich_job
                job_data = enrich_job(job_data)
            except Exception as e:
                print(f"  enrich error: {e}")

            posted_raw = job_data.get("posted_date")
            posted_date = None
            if posted_raw:
                if isinstance(posted_raw, str):
                    try:
                        posted_date = datetime.fromisoformat(posted_raw.replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        posted_date = None
                elif isinstance(posted_raw, datetime):
                    posted_date = posted_raw

            ext_id = job_data.get("external_id", "")
            existing_job = self.db.query(Job).filter_by(
                source_id=source_id, external_id=ext_id
            ).first() if ext_id else None

            if existing_job:
                existing_job.title = job_data.get("title", existing_job.title)
                existing_job.company = job_data.get("company", existing_job.company)
                existing_job.location = job_data.get("location", existing_job.location)
                existing_job.remote = job_data.get("remote", existing_job.remote)
                existing_job.hybrid = job_data.get("hybrid", existing_job.hybrid)
                existing_job.external_url = job_data.get("external_url", existing_job.external_url)
                existing_job.description = job_data.get("description", existing_job.description)
                existing_job.seniority = job_data.get("seniority") or existing_job.seniority
                existing_job.employment_type = job_data.get("employment_type") or existing_job.employment_type
                existing_job.min_salary = job_data.get("min_salary") or existing_job.min_salary
                existing_job.max_salary = job_data.get("max_salary") or existing_job.max_salary
                existing_job.skills_required = job_data.get("skills_required") or existing_job.skills_required
                existing_job.experience_years_min = job_data.get("experience_years_min") or existing_job.experience_years_min
                existing_job.experience_years_max = job_data.get("experience_years_max") or existing_job.experience_years_max
                existing_job.visa_sponsorship = job_data.get("visa_sponsorship")
                existing_job.industry = job_data.get("industry") or existing_job.industry
                existing_job.company_size = job_data.get("company_size") or existing_job.company_size
                existing_job.benefits_extracted = job_data.get("benefits_extracted") or existing_job.benefits_extracted
                existing_job.scraped_at = datetime.utcnow()
                existing_job.is_active = True
                self.db.commit()
                job_ids.append(existing_job.id)
            else:
                job = Job(
                    source_id=source_id,
                    external_id=ext_id,
                    external_url=job_data.get("external_url", ""),
                    title=job_data.get("title", ""),
                    company=job_data.get("company", ""),
                    location=job_data.get("location", ""),
                    remote=job_data.get("remote", False),
                    hybrid=job_data.get("hybrid", False),
                    description=job_data.get("description", ""),
                    department=job_data.get("department", ""),
                    seniority=job_data.get("seniority", ""),
                    employment_type=job_data.get("employment_type", "full_time"),
                    min_salary=job_data.get("min_salary"),
                    max_salary=job_data.get("max_salary"),
                    skills_required=job_data.get("skills_required", []),
                    experience_years_min=job_data.get("experience_years_min"),
                    experience_years_max=job_data.get("experience_years_max"),
                    visa_sponsorship=job_data.get("visa_sponsorship"),
                    industry=job_data.get("industry"),
                    company_size=job_data.get("company_size"),
                    benefits_extracted=job_data.get("benefits_extracted", []),
                    scraped_at=datetime.utcnow(),
                    posted_date=posted_date,
                    is_active=True
                )
                self.db.add(job)
                self.db.commit()
                self.db.refresh(job)
                job_ids.append(job.id)

        return job_ids
    
    def _update_cache(
        self,
        user_id: int,
        preferences: UserPreferences,
        job_ids: List[int],
        search_duration_ms: int
    ) -> SearchCache:
        """Update or create cache entry"""
        cache_key = SearchCache.create_cache_key(preferences.to_dict())
        
        # Check if cache exists
        existing = self.db.query(SearchCache).filter_by(
            user_id=user_id,
            search_key=cache_key
        ).first()
        
        if existing:
            # Update existing
            existing.job_ids = job_ids
            existing.total_results = len(job_ids)
            existing.expires_at = datetime.utcnow() + timedelta(hours=24)
            existing.is_valid = True
            existing.search_duration_ms = search_duration_ms
            existing.jobs_found = len(job_ids)
            cache = existing
        else:
            # Create new
            cache = SearchCache.create_from_search(
                user_id=user_id,
                params=preferences.to_dict(),
                job_ids=job_ids,
                ttl_hours=24,
                search_duration_ms=search_duration_ms
            )
            self.db.add(cache)
        
        # Update preferences last_search_run
        preferences.last_search_run = datetime.utcnow()
        
        self.db.commit()
        
        return cache
    
    def _fetch_jobs_by_ids(self, job_ids: List[int]) -> List[Dict]:
        """Fetch full job objects by IDs"""
        if not job_ids:
            return []
        
        jobs = self.db.query(Job).filter(
            Job.id.in_(job_ids[:50]),  # Limit to 50 jobs for display
            Job.is_active == True
        ).all()
        
        return [self._job_to_dict(job) for job in jobs]
    
    def _job_to_dict(self, job: Job) -> Dict:
        """Convert Job model to dictionary (includes enriched fields for matching)"""
        return {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "remote": job.remote,
            "hybrid": job.hybrid,
            "min_salary": job.min_salary,
            "max_salary": job.max_salary,
            "salary_currency": job.salary_currency,
            "seniority": job.seniority,
            "department": job.department,
            "employment_type": job.employment_type,
            "description": job.description[:500] + "..." if job.description and len(job.description) > 500 else job.description,
            "external_url": job.external_url,
            "posted_date": job.posted_date.isoformat() if job.posted_date else None,
            "source": job.source.name if job.source else "unknown",
            # Enriched fields for 1:1 matching
            "skills_required": job.skills_required or [],
            "experience_years_min": job.experience_years_min,
            "experience_years_max": job.experience_years_max,
            "visa_sponsorship": job.visa_sponsorship,
            "industry": job.industry,
            "company_size": job.company_size,
            "benefits_extracted": job.benefits_extracted or [],
        }
    
    def _get_sources_used(self, jobs: List[Dict]) -> Dict[str, int]:
        """Count jobs by source"""
        sources = {}
        for job in jobs:
            source = job.get("_source", "unknown")
            sources[source] = sources.get(source, 0) + 1
        return sources
