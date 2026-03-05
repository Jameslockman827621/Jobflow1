"""
Lever ATS Scraper

Lever powers 10,000+ company career pages.
URL pattern: https://api.lever.co/v0/postings/{company}
API is public for embedding.
"""

from typing import List, Dict
from datetime import datetime
import httpx

from .base import BaseScraper, JobData


class LeverScraper(BaseScraper):
    name = "lever"
    base_url = "https://api.lever.co/v0/postings"
    
    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        """Scrape jobs for a specific company"""
        url = f"{self.base_url}/{company_subdomain}"
        
        async with httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
        ) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                return [self._parse_job(job, company_subdomain) for job in data]
            except Exception as e:
                print(f"Error scraping {company_subdomain}: {e}")
                return []
    
    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        """Lever doesn't have global search - needs company list"""
        print("Lever: scrape_all_jobs not implemented - needs company list")
        return []
    
    def _parse_job(self, job: Dict, company: str) -> JobData:
        """Parse Lever job API response"""
        location = ""
        remote = False
        hybrid = False
        
        # Parse location
        location_data = job.get("locations", {})
        if isinstance(location_data, list):
            location = location_data[0] if location_data else ""
        else:
            location = location_data.get("text", "") if location_data else ""
        
        remote = "remote" in location.lower() if location else False
        hybrid = "hybrid" in location.lower() if location else False
        
        # Parse department
        department = job.get("departments", [{}])[0].get("text") if job.get("departments") else None
        
        # Parse seniority
        seniority = self.parse_seniority(job.get("title", ""))
        
        return JobData(
            title=job.get("title", ""),
            company=company,
            location=location,
            external_id=job.get("id", ""),
            external_url=job.get("hostedUrl", ""),
            description=job.get("description", ""),
            remote=remote,
            hybrid=hybrid,
            department=department,
            seniority=seniority,
            posted_date=datetime.fromisoformat(job["updatedAt"].replace("Z", "+00:00")) if job.get("updatedAt") else None,
            raw_data=job,
        )
