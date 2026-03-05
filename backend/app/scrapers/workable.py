"""
Workable Scraper

Workable powers 100,000+ company career pages.
No public API - requires HTML scraping.
URL pattern: https://company.workable.com/api/v2/jobs
"""

from typing import List, Dict
from datetime import datetime
from bs4 import BeautifulSoup

from .base import BaseScraper, JobData


class WorkableScraper(BaseScraper):
    name = "workable"
    base_url = "https://www.workable.com/api/v2/jobs"
    
    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        """Scrape jobs for a specific company"""
        url = f"https://{company_subdomain}.workable.com/api/v2/jobs"
        
        html = await self.fetch(url)
        if not html:
            return []
        
        try:
            data = BeautifulSoup(html, 'lxml')
            # Workable API returns JSON in most cases
            import json
            jobs_data = json.loads(data.text if hasattr(data, 'text') else html)
            return [self._parse_job(job, company_subdomain) for job in jobs_data.get("jobs", [])]
        except Exception as e:
            print(f"Error parsing Workable response: {e}")
            return []
    
    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        """Workable doesn't have global search - needs company list"""
        print("Workable: scrape_all_jobs not implemented - needs company list")
        return []
    
    def _parse_job(self, job: Dict, company: str) -> JobData:
        """Parse Workable job data"""
        location = job.get("location", "")
        remote = "remote" in location.lower() if location else False
        hybrid = "hybrid" in location.lower() if location else False
        
        return JobData(
            title=job.get("title", ""),
            company=company,
            location=location,
            external_id=str(job.get("id", "")),
            external_url=job.get("url", ""),
            description=job.get("description", ""),
            remote=remote,
            hybrid=hybrid,
            seniority=self.parse_seniority(job.get("title", "")),
            raw_data=job,
        )
