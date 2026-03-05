"""
Greenhouse ATS Scraper

Greenhouse powers 40,000+ company career pages.
URL pattern: https://boards-api.greenhouse.io/v1/boards/{company}/jobs
API is public and intended for embedding - no auth required.
"""

from typing import List, Dict, Optional
from datetime import datetime
import httpx

from .base import BaseScraper, JobData


class GreenhouseScraper(BaseScraper):
    name = "greenhouse"
    base_url = "https://boards-api.greenhouse.io/v1/boards"
    
    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        """Scrape jobs for a specific company"""
        url = f"{self.base_url}/{company_subdomain}/jobs"
        params = {"content": "true"}  # Include full job descriptions
        
        async with httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True,
        ) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                jobs = data.get("jobs", [])
                print(f"  API returned {len(jobs)} jobs for {company_subdomain}")
                return [self._parse_job(job, company_subdomain) for job in jobs]
            except httpx.HTTPStatusError as e:
                print(f"HTTP error for {company_subdomain}: {e.response.status_code}")
                return []
            except Exception as e:
                print(f"Error scraping {company_subdomain}: {e}")
                return []
    
    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        """
        Greenhouse doesn't have a global job search endpoint.
        This would require a list of known company subdomains.
        For MVP, we'll maintain a curated list or use job board aggregators.
        """
        # TODO: Implement with curated company list
        print("Greenhouse: scrape_all_jobs not implemented - needs company list")
        return []
    
    def _parse_job(self, job: Dict, company: str) -> JobData:
        """Parse Greenhouse job API response"""
        location = ""
        remote = False
        hybrid = False
        
        # Parse locations
        locations = job.get("locations", [])
        if locations:
            location = locations[0].get("name", "")
            remote = "Remote" in location or "remote" in location.lower()
            hybrid = "Hybrid" in location
        
        # Parse departments
        departments = job.get("departments", [])
        department = departments[0].get("name") if departments else None
        
        # Parse seniority from title
        seniority = self.parse_seniority(job.get("title", ""))
        
        # Parse salary (if available)
        min_salary = None
        max_salary = None
        
        # Parse description - Greenhouse returns it as HTML
        description_obj = job.get("description", {})
        description = ""
        if isinstance(description_obj, dict):
            description = description_obj.get("content", "")
            # Also try to get plain text version
            if not description:
                description = description_obj.get("text", "")
        elif isinstance(description_obj, str):
            description = description_obj
        
        return JobData(
            title=job.get("title", "") or "Unknown Position",
            company=company,
            location=location,
            external_id=str(job.get("id", "")),
            external_url=job.get("absolute_url", ""),
            description=description,
            remote=remote,
            hybrid=hybrid,
            min_salary=min_salary,
            max_salary=max_salary,
            department=department,
            seniority=seniority,
            posted_date=datetime.fromisoformat(job["updated_at"]) if job.get("updated_at") else None,
            raw_data=job,
        )
