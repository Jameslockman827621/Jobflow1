"""
On-Demand Job Search Service

Runs targeted job searches based on user preferences.
Replaces continuous background scraping with just-in-time searches.
"""

import asyncio
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.job import Job, JobSource
from app.models.preferences import UserPreferences
from app.models.search_cache import SearchCache
from app.scrapers.apify_linkedin import ApifyLinkedInScraper
from app.scrapers.apify_indeed import ApifyIndeedScraper
from app.scrapers.greenhouse import GreenhouseScraper
from app.scrapers.lever import LeverScraper
from app.core.config import settings


class OnDemandSearchService:
    """
    Runs job searches on-demand based on user preferences.
    
    Flow:
    1. Check cache (if valid, return cached results)
    2. If expired/missing, run searches across sources
    3. Deduplicate results
    4. Cache results
    5. Return fresh jobs
    
    Sources:
    - LinkedIn (via Apify)
    - Indeed (via Apify)
    - Greenhouse (direct API)
    - Lever (direct scraping)
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.linkedin_scraper = None
        self.indeed_scraper = None
        self.greenhouse_scraper = GreenhouseScraper()
        self.lever_scraper = LeverScraper()
        
        if settings.APIFY_API_KEY:
            self.linkedin_scraper = ApifyLinkedInScraper(api_key=settings.APIFY_API_KEY)
            self.indeed_scraper = ApifyIndeedScraper(api_key=settings.APIFY_API_KEY)
    
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
        
        # Run fresh search
        search_start = time.time()
        jobs = await self._run_searches(preferences)
        search_duration_ms = int((time.time() - search_start) * 1000)
        
        # Deduplicate
        jobs = self._deduplicate_jobs(jobs)
        
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
            "message": f"Fresh search completed in {total_duration_ms}ms",
            "jobs": job_objects,
            "total": len(job_objects),
            "cache": cache.to_dict(),
            "search_duration_ms": search_duration_ms,
            "sources_used": self._get_sources_used(jobs)
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
    
    async def _run_searches(self, preferences: UserPreferences) -> List[Dict]:
        """
        Run searches across all sources based on preferences.
        
        Sources:
        1. LinkedIn (via Apify) - broad search
        2. Indeed (via Apify) - broad search, fast
        3. Greenhouse - target companies
        4. Lever - target companies
        """
        all_jobs = []
        
        # 1. LinkedIn search (if API key available)
        if self.linkedin_scraper and preferences.target_roles:
            linkedin_jobs = await self._search_linkedin(preferences)
            all_jobs.extend(linkedin_jobs)
        
        # 2. Indeed search (if API key available) - FAST!
        if self.indeed_scraper and preferences.target_roles:
            indeed_jobs = await self._search_indeed(preferences)
            all_jobs.extend(indeed_jobs)
        
        # 3. Greenhouse company searches
        if preferences.target_companies:
            greenhouse_jobs = await self._search_greenhouse(preferences)
            all_jobs.extend(greenhouse_jobs)
        
        # 4. Lever company searches
        if preferences.target_companies:
            lever_jobs = await self._search_lever(preferences)
            all_jobs.extend(lever_jobs)
        
        return all_jobs
    
    async def _search_linkedin(self, preferences: UserPreferences) -> List[Dict]:
        """Search LinkedIn for jobs matching preferences"""
        jobs = []
        
        for role in preferences.target_roles[:3]:  # Limit to 3 roles to avoid rate limits
            for location in preferences.locations[:2]:  # Limit to 2 locations
                try:
                    search_jobs = await self.linkedin_scraper.search_jobs(
                        keywords=role,
                        location=location,
                        max_jobs=50,
                        remote=preferences.remote_only or preferences.hybrid_ok
                    )
                    
                    for job in search_jobs:
                        job_dict = job.to_dict()
                        job_dict["_source"] = "linkedin"
                        jobs.append(job_dict)
                        
                except Exception as e:
                    print(f"LinkedIn search error ({role} in {location}): {e}")
                    continue
        
        return jobs
    
    async def _search_indeed(self, preferences: UserPreferences) -> List[Dict]:
        """Search Indeed for jobs matching preferences"""
        jobs = []
        
        for role in preferences.target_roles[:5]:  # Indeed is fast, can do more
            for location in preferences.locations[:3]:  # Up to 3 locations
                try:
                    # Extract country from location (default to UK)
                    country = "uk"
                    if "us" in location.lower() or "usa" in location.lower():
                        country = "us"
                    elif "canada" in location.lower():
                        country = "ca"
                    
                    search_jobs = await self.indeed_scraper.search_jobs(
                        query=role,
                        location=location.split(",")[0].strip(),  # Just city name
                        country=country,
                        max_jobs=30,  # Indeed is fast, get good coverage
                        remote="remote" if preferences.remote_only else None,
                        job_type="fulltime" if "FULL_TIME" in preferences.employment_types else "parttime",
                        from_days=14  # Last 2 weeks
                    )
                    
                    for job in search_jobs:
                        job_dict = job.to_dict()
                        job_dict["_source"] = "indeed"
                        jobs.append(job_dict)
                        
                except Exception as e:
                    print(f"Indeed search error ({role} in {location}): {e}")
                    continue
        
        return jobs
    
    async def _search_greenhouse(self, preferences: UserPreferences) -> List[Dict]:
        """Search Greenhouse for target companies"""
        jobs = []
        
        for company in preferences.target_companies[:10]:  # Limit to 10 companies
            try:
                company_jobs = await self.greenhouse_scraper.scrape_company_jobs(company.lower())
                
                for job in company_jobs:
                    job_dict = job.to_dict()
                    job_dict["_source"] = "greenhouse"
                    jobs.append(job_dict)
                    
            except Exception as e:
                print(f"Greenhouse search error ({company}): {e}")
                continue
        
        return jobs
    
    async def _search_lever(self, preferences: UserPreferences) -> List[Dict]:
        """Search Lever for target companies"""
        jobs = []
        
        for company in preferences.target_companies[:10]:  # Limit to 10 companies
            try:
                company_jobs = await self.lever_scraper.scrape_company_jobs(company.lower())
                
                for job in company_jobs:
                    job_dict = job.to_dict()
                    job_dict["_source"] = "lever"
                    jobs.append(job_dict)
                    
            except Exception as e:
                print(f"Lever search error ({company}): {e}")
                continue
        
        return jobs
    
    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Deduplicate jobs across sources.
        
        Priority: LinkedIn > Greenhouse > Lever
        (LinkedIn has most complete data)
        """
        seen_urls = set()
        deduplicated = []
        
        # Sort by source priority
        source_priority = {"linkedin": 0, "greenhouse": 1, "lever": 2}
        jobs_sorted = sorted(jobs, key=lambda j: source_priority.get(j.get("_source", ""), 99))
        
        for job in jobs_sorted:
            url = job.get("external_url", "")
            
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduplicated.append(job)
            elif not url:
                # No URL, use company + title as fallback
                key = f"{job.get('company', '')}|{job.get('title', '')}"
                if key not in seen_urls:
                    seen_urls.add(key)
                    deduplicated.append(job)
        
        return deduplicated
    
    def _save_jobs(self, jobs: List[Dict]) -> List[int]:
        """
        Save jobs to database and return IDs.
        
        Uses upsert (merge) to avoid duplicates.
        """
        job_ids = []
        
        # Get or create job sources
        sources = {}
        for source_name in ["linkedin", "greenhouse", "lever"]:
            source = self.db.query(JobSource).filter_by(name=source_name).first()
            if not source:
                source = JobSource(
                    name=source_name,
                    base_url=f"https://{source_name}.com",
                    is_active=True
                )
                self.db.add(source)
                self.db.commit()
            sources[source_name] = source
        
        for job_data in jobs:
            source_name = job_data.pop("_source", "unknown")
            source_id = sources.get(source_name, sources.get("linkedin")).id
            
            job = Job(
                source_id=source_id,
                external_id=job_data.get("external_id", ""),
                external_url=job_data.get("external_url", ""),
                title=job_data.get("title", ""),
                company=job_data.get("company", ""),
                location=job_data.get("location", ""),
                remote=job_data.get("remote", False),
                hybrid=job_data.get("hybrid", False),
                description=job_data.get("description", ""),
                department=job_data.get("department", ""),
                seniority=job_data.get("seniority", ""),
                min_salary=job_data.get("min_salary"),
                max_salary=job_data.get("max_salary"),
                scraped_at=datetime.utcnow(),
                posted_date=job_data.get("posted_date"),
                is_active=True
            )
            
            self.db.merge(job)
            self.db.commit()
            
            if job.id:
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
        """Convert Job model to dictionary"""
        return {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "remote": job.remote,
            "hybrid": job.hybrid,
            "min_salary": job.min_salary,
            "max_salary": job.max_salary,
            "seniority": job.seniority,
            "department": job.department,
            "description": job.description[:500] + "..." if job.description and len(job.description) > 500 else job.description,
            "external_url": job.external_url,
            "posted_date": job.posted_date.isoformat() if job.posted_date else None,
            "source": job.source.name if job.source else "unknown",
        }
    
    def _get_sources_used(self, jobs: List[Dict]) -> Dict[str, int]:
        """Count jobs by source"""
        sources = {}
        for job in jobs:
            source = job.get("_source", "unknown")
            sources[source] = sources.get(source, 0) + 1
        return sources
    
    def _get_sources_used(self, jobs: List[Dict]) -> Dict[str, int]:
        """Count jobs by source"""
        sources = {}
        for job in jobs:
            source = job.get("_source", "unknown")
            sources[source] = sources.get(source, 0) + 1
        return sources
