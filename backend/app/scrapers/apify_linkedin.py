"""
Apify LinkedIn Jobs Scraper Integration

Uses official Apify Python client for better error handling and async support.

Actor: hKByXkMQaC5Qt9UMN
Docs: https://apify.com/apify/linkedin-jobs-scraper

Usage:
    from app.scrapers.apify_linkedin import ApifyLinkedInScraper
    
    scraper = ApifyLinkedInScraper(api_key=settings.APIFY_API_KEY)
    jobs = await scraper.search_jobs(
        keywords="Software Engineer",
        location="United Kingdom",
        max_jobs=100
    )
"""

import asyncio
from typing import List, Optional
from datetime import datetime, timedelta
from apify_client import ApifyClientAsync

from .base import BaseScraper, JobData


class ApifyLinkedInScraper(BaseScraper):
    """
    LinkedIn Jobs Scraper via Apify API
    
    Provides access to LinkedIn's job postings without direct scraping.
    Handles proxy rotation, rate limiting, and anti-bot measures automatically.
    """
    
    name = "apify_linkedin"
    base_url = "https://www.linkedin.com/jobs"
    actor_id = "hKByXkMQaC5Qt9UMN"
    
    def __init__(self, api_key: str):
        """
        Initialize Apify LinkedIn Scraper
        
        Args:
            api_key: Apify API key (apify_api_...)
        """
        self.api_key = api_key
        self.client = ApifyClientAsync(token=api_key)
    
    async def search_jobs(
        self,
        keywords: str,
        location: str = "",
        max_jobs: int = 100,
        date_posted: str = "month",
        job_type: str = "fulltime",
        remote: bool = True,
    ) -> List[JobData]:
        """
        Search LinkedIn jobs via Apify
        
        Args:
            keywords: Job search keywords (e.g., "Software Engineer")
            location: Location filter (e.g., "United Kingdom", "London")
            max_jobs: Maximum number of jobs to scrape (default: 100)
            date_posted: Time filter - "anytime", "month", "week", "day"
            job_type: Job type - "fulltime", "parttime", "contract", "internship"
            remote: Include remote jobs
        
        Returns:
            List of JobData objects
        """
        # Build LinkedIn search URL
        url = self._build_linkedin_url(keywords, location, date_posted, job_type, remote)
        
        actor_input = {
            "urls": [url],
            "scrapeCompany": True,
            "count": max_jobs,
            "splitByLocation": False
        }
        
        try:
            # Start the actor run
            run = await self.client.actor(self.actor_id).call(input=actor_input)
            
            # Wait for completion with timeout
            completed_run = await self.client.run(run["id"]).wait_for_finish(timeout_secs=900)
            
            if not completed_run:
                raise Exception(f"Apify run timed out after 15 minutes")
            
            if completed_run["status"] != "SUCCEEDED":
                raise Exception(f"Apify run failed with status: {completed_run['status']}")
            
            # Fetch results
            items = []
            async for item in self.client.dataset(completed_run["defaultDatasetId"]).iterate_items():
                items.append(item)
            
            # Convert to JobData objects
            jobs = [self._parse_job(item) for item in items]
            return [j for j in jobs if j is not None]
            
        except Exception as e:
            print(f"Error scraping LinkedIn jobs: {e}")
            return []
    
    def _build_linkedin_url(
        self,
        keywords: str,
        location: str = "",
        date_posted: str = "month",
        job_type: str = "fulltime",
        remote: bool = True,
    ) -> str:
        """
        Build LinkedIn jobs search URL
        
        LinkedIn URL format:
        https://www.linkedin.com/jobs/search/?keywords=...&location=...&f_TPR=...&f_JT=...&f_WT=...
        """
        base = "https://www.linkedin.com/jobs/search/"
        params = []
        
        # Keywords
        params.append(f"keywords={keywords.replace(' ', '%20')}")
        
        # Location
        if location:
            params.append(f"location={location.replace(' ', '%20')}")
        
        # Date posted (f_TPR)
        date_filters = {
            "anytime": "",
            "month": "r2592000",  # Last 30 days
            "week": "r604800",    # Last 7 days
            "day": "r86400"       # Last 24 hours
        }
        if date_filters.get(date_posted):
            params.append(f"f_TPR={date_filters[date_posted]}")
        
        # Job type (f_JT)
        job_filters = {
            "fulltime": "F",
            "parttime": "P",
            "contract": "C",
            "internship": "I"
        }
        if job_filters.get(job_type):
            params.append(f"f_JT={job_filters[job_type]}")
        
        # Remote (f_WT)
        if remote:
            params.append("f_WT=2")  # Remote only
        
        # Position and page
        params.append("position=1")
        params.append("pageNum=0")
        
        return base + "?".join([params[0], "&".join(params[1:])])
    
    def _parse_job(self, job_data: dict) -> Optional[JobData]:
        """
        Convert Apify response to normalized JobData object
        
        Args:
            job_data: Raw job data from Apify
        
        Returns:
            JobData object or None if parsing fails
        """
        try:
            # Extract salary if available
            min_salary = None
            max_salary = None
            if job_data.get("salaryInfo"):
                salary_text = job_data["salaryInfo"]
                min_salary, max_salary = self.parse_salary(salary_text)
            
            # Parse posted date
            posted_date = None
            if job_data.get("postedAt"):
                try:
                    posted_date = datetime.fromisoformat(job_data["postedAt"].replace("Z", "+00:00"))
                except:
                    posted_date = self._parse_relative_date(job_data.get("postedAt", ""))
            
            # Determine remote/hybrid
            is_remote = "remote" in job_data.get("employmentType", "").lower()
            is_remote = is_remote or "remote" in job_data.get("jobFunction", "").lower()
            
            return JobData(
                title=job_data.get("title", ""),
                company=job_data.get("companyName", ""),
                location=job_data.get("location", ""),
                external_id=str(job_data.get("id", "")),
                external_url=job_data.get("link", ""),
                description=job_data.get("descriptionText", ""),
                remote=is_remote,
                hybrid=False,  # LinkedIn doesn't explicitly mark hybrid
                min_salary=min_salary,
                max_salary=max_salary,
                department=job_data.get("jobFunction", ""),
                seniority=job_data.get("seniorityLevel", ""),
                posted_date=posted_date,
                raw_data=job_data
            )
        except Exception as e:
            print(f"Error parsing job data: {e}")
            return None
    
    def _parse_relative_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse LinkedIn relative date format (e.g., '2 days ago', '1 week ago')
        
        Args:
            date_str: Relative date string
        
        Returns:
            datetime object or None
        """
        if not date_str:
            return None
        
        import re
        
        now = datetime.utcnow()
        
        # Match patterns like "2 days ago", "1 week ago", "3 hours ago"
        match = re.search(r'(\d+)\s*(hour|day|week|month)s?\s*ago', date_str.lower())
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            
            if unit == "hour":
                return now - timedelta(hours=value)
            elif unit == "day":
                return now - timedelta(days=value)
            elif unit == "week":
                return now - timedelta(weeks=value)
            elif unit == "month":
                return now - timedelta(days=value * 30)
        
        return None
    
    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        """
        Not implemented for LinkedIn - use search_jobs() instead
        
        LinkedIn doesn't support company-based scraping via URL pattern.
        Use search_jobs with company name as keyword instead.
        """
        raise NotImplementedError(
            "Use search_jobs(keywords='Software Engineer at {company}') for LinkedIn"
        )
    
    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        """
        Not implemented for LinkedIn - use search_jobs() with specific keywords
        
        LinkedIn requires specific search terms.
        """
        raise NotImplementedError(
            "Use search_jobs() with specific keywords for LinkedIn"
        )
    
    async def search_multiple(
        self,
        searches: List[dict],
        max_per_search: int = 50,
    ) -> List[JobData]:
        """
        Run multiple searches in parallel
        
        Args:
            searches: List of search configs, each with keywords, location, etc.
            max_per_search: Max jobs per search
        
        Returns:
            Combined list of all jobs (deduplicated)
        """
        tasks = [
            self.search_jobs(
                keywords=search.get("keywords", ""),
                location=search.get("location", ""),
                max_jobs=max_per_search,
                date_posted=search.get("date_posted", "month"),
                job_type=search.get("job_type", "fulltime"),
                remote=search.get("remote", True),
            )
            for search in searches
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and deduplicate
        all_jobs = []
        seen_ids = set()
        
        for result in results:
            if isinstance(result, Exception):
                print(f"Search failed: {result}")
                continue
            
            for job in result:
                if job.external_id not in seen_ids:
                    seen_ids.add(job.external_id)
                    all_jobs.append(job)
        
        return all_jobs
