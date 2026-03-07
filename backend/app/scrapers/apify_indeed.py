"""
Apify Indeed Jobs Scraper Integration

Uses official Apify Python client for Indeed job scraping.

Actor: MXLpngmVpE8WTESQr
Docs: https://apify.com/apify/indeed-scraper

Usage:
    from app.scrapers.apify_indeed import ApifyIndeedScraper
    
    scraper = ApifyIndeedScraper(api_key=settings.APIFY_API_KEY)
    jobs = await scraper.search_jobs(
        query="Business Development Representative",
        location="Oxford",
        country="uk",
        max_jobs=50
    )
"""

import asyncio
from typing import List, Optional
from datetime import datetime, timedelta
from apify_client import ApifyClientAsync

from .base import BaseScraper, JobData


class ApifyIndeedScraper(BaseScraper):
    """
    Indeed Jobs Scraper via Apify API
    
    Provides access to Indeed's job postings without direct scraping.
    Handles proxy rotation, rate limiting, and anti-bot measures automatically.
    
    Supports:
    - Country-specific searches (us, uk, ca, au, de, etc.)
    - Location-based searches with radius
    - Remote/hybrid filtering
    - Job type filtering (fulltime, parttime, contract)
    - Date range filtering (last 1-30 days)
    - Seniority level filtering
    """
    
    name = "apify_indeed"
    base_url = "https://www.indeed.com"
    actor_id = "MXLpngmVpE8WTESQr"
    
    # Supported countries
    COUNTRIES = ["us", "uk", "ca", "au", "de", "fr", "ie", "nl", "in", "sg"]
    
    # Supported job types
    JOB_TYPES = ["fulltime", "parttime", "contract", "internship", "temporary"]
    
    # Supported seniority levels
    LEVELS = ["entry_level", "mid_level", "senior_level", "director", "executive"]
    
    def __init__(self, api_key: str):
        """
        Initialize Apify Indeed Scraper
        
        Args:
            api_key: Apify API key (apify_api_...)
        """
        self.api_key = api_key
        self.client = ApifyClientAsync(token=api_key)
    
    async def search_jobs(
        self,
        query: str,
        location: str = "",
        country: str = "uk",
        max_jobs: int = 50,
        remote: Optional[str] = None,  # "remote", "hybrid", or None
        job_type: str = "fulltime",
        from_days: int = 14,
        sort: str = "relevance",
    ) -> List[JobData]:
        """
        Search Indeed jobs via Apify
        
        Args:
            query: Job search query (e.g., "Software Engineer")
            location: Location (e.g., "Oxford", "London")
            country: Country code (us, uk, ca, au, de, fr, etc.)
            max_jobs: Maximum number of jobs to scrape (default: 50)
            remote: Remote filter - "remote", "hybrid", or None for all
            job_type: Job type (fulltime, parttime, contract, etc.)
            from_days: Only jobs posted in last N days (1-30)
            sort: Sort order (relevance, date)
        
        Returns:
            List of JobData objects
        """
        # Validate inputs
        if country not in self.COUNTRIES:
            print(f"Warning: Country '{country}' not in supported list, using 'uk'")
            country = "uk"
        
        if job_type not in self.JOB_TYPES:
            job_type = "fulltime"
        
        # Build actor input
        actor_input = {
            "country": country,
            "query": query,
            "location": location,
            "maxRows": max_jobs,
            "sort": sort,
            "jobType": job_type,
            "fromDays": str(min(max(from_days, 1), 30)),  # Clamp to 1-30
            "enableUniqueJobs": True,
            "includeSimilarJobs": True,
        }
        
        # Add remote filter if specified
        if remote in ["remote", "hybrid"]:
            actor_input["remote"] = remote
        
        try:
            # Start the actor run
            run = await self.client.actor(self.actor_id).call(input=actor_input)
            
            # Wait for completion with timeout (Indeed is usually fast - 30-60s)
            completed_run = await self.client.run(run["id"]).wait_for_finish(timeout_secs=300)
            
            if not completed_run:
                raise Exception(f"Apify Indeed run timed out after 5 minutes")
            
            if completed_run["status"] != "SUCCEEDED":
                raise Exception(f"Apify Indeed run failed with status: {completed_run['status']}")
            
            # Fetch results
            items = []
            async for item in self.client.dataset(completed_run["defaultDatasetId"]).iterate_items():
                items.append(item)
            
            # Convert to JobData objects
            jobs = [self._parse_job(item) for item in items]
            return [j for j in jobs if j is not None]
            
        except Exception as e:
            print(f"Error scraping Indeed jobs: {e}")
            return []
    
    def _parse_job(self, job_data: dict) -> Optional[JobData]:
        """
        Convert Apify Indeed response to normalized JobData object
        
        Args:
            job_data: Raw job data from Apify
        
        Returns:
            JobData object or None if parsing fails
        """
        try:
            # Extract location (Indeed returns as dict)
            location_data = job_data.get("location", {})
            if isinstance(location_data, dict):
                city = location_data.get("city", "")
                country = location_data.get("country", "")
                location = f"{city}, {country}" if city and country else str(location_data)
            else:
                location = str(location_data) if location_data else ""
            
            # Extract salary (Indeed returns as dict)
            salary_data = job_data.get("salary", {})
            min_salary = None
            max_salary = None
            salary_currency = "GBP"
            
            if isinstance(salary_data, dict):
                min_salary = salary_data.get("salaryMin")
                max_salary = salary_data.get("salaryMax")
                salary_currency = salary_data.get("salaryCurrency", "GBP")
            
            # Parse posted date
            posted_date = None
            if job_data.get("datePublished"):
                try:
                    posted_date = datetime.fromisoformat(job_data["datePublished"].replace("Z", "+00:00"))
                except:
                    posted_date = datetime.utcnow()
            
            # Determine remote/hybrid
            is_remote = job_data.get("isRemote", False)
            is_hybrid = False
            
            # Check attributes for remote/hybrid
            attributes = job_data.get("attributes", [])
            if isinstance(attributes, list):
                is_remote = is_remote or "remote" in [str(a).lower() for a in attributes]
                is_hybrid = "hybrid" in [str(a).lower() for a in attributes]
            
            # Extract company info
            company = job_data.get("companyName", "")
            if not company:
                company = job_data.get("company", "")
            
            return JobData(
                title=job_data.get("title", ""),
                company=company,
                location=location,
                external_id=str(job_data.get("jobKey", "")),
                external_url=job_data.get("jobUrl", ""),
                description=job_data.get("descriptionText", ""),
                remote=is_remote,
                hybrid=is_hybrid,
                min_salary=min_salary,
                max_salary=max_salary,
                seniority=self._extract_seniority(job_data.get("title", "")),
                posted_date=posted_date,
                raw_data=job_data
            )
        except Exception as e:
            print(f"Error parsing Indeed job data: {e}")
            return None
    
    def _extract_seniority(self, title: str) -> Optional[str]:
        """Extract seniority level from job title"""
        title_lower = title.lower()
        
        if any(x in title_lower for x in ["executive", "c-level", "cto", "ceo"]):
            return "executive"
        elif any(x in title_lower for x in ["vp", "vice president"]):
            return "executive"
        elif any(x in title_lower for x in ["director", "head of"]):
            return "lead"
        elif any(x in title_lower for x in ["senior", "sr.", "sr "]):
            return "senior"
        elif any(x in title_lower for x in ["junior", "jr.", "jr ", "entry", "graduate"]):
            return "entry"
        elif any(x in title_lower for x in ["lead", "principal", "staff"]):
            return "lead"
        else:
            return "mid"
    
    async def search_multiple(
        self,
        searches: List[dict],
        max_per_search: int = 50,
    ) -> List[JobData]:
        """
        Run multiple searches in parallel
        
        Args:
            searches: List of search configs
            max_per_search: Max jobs per search
        
        Returns:
            Combined list of all jobs (deduplicated)
        """
        tasks = [
            self.search_jobs(
                query=search.get("query", ""),
                location=search.get("location", ""),
                country=search.get("country", "uk"),
                max_jobs=max_per_search,
                remote=search.get("remote"),
                job_type=search.get("job_type", "fulltime"),
                from_days=search.get("from_days", 14),
            )
            for search in searches
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and deduplicate
        all_jobs = []
        seen_ids = set()
        
        for result in results:
            if isinstance(result, Exception):
                print(f"Indeed search failed: {result}")
                continue
            
            for job in result:
                if job.external_id not in seen_ids:
                    seen_ids.add(job.external_id)
                    all_jobs.append(job)
        
        return all_jobs
