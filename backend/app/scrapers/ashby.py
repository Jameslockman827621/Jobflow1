"""
Ashby ATS Scraper

Ashby powers modern startup career pages.
Public job board API: https://api.ashbyhq.com/posting-api/job-board/{slug}
"""

from typing import List, Dict, Optional
from datetime import datetime
import httpx

from .base import BaseScraper, JobData


class AshbyScraper(BaseScraper):
    name = "ashby"
    base_url = "https://api.ashbyhq.com/posting-api/job-board"

    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        url = f"{self.base_url}/{company_subdomain}"
        params = {"includeCompensation": "true"}

        async with httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True,
        ) as client:
            try:
                response = await client.get(url, params=params)
                if response.status_code == 404:
                    print(f"  {company_subdomain}: Not on Ashby")
                    return []
                response.raise_for_status()
                data = response.json()
                jobs = data.get("jobs", []) or data.get("jobPostings", []) or []
                print(f"  {company_subdomain}: Found {len(jobs)} Ashby jobs")
                return [self._parse_job(job, company_subdomain) for job in jobs]
            except httpx.HTTPStatusError as e:
                print(f"HTTP error for Ashby {company_subdomain}: {e.response.status_code}")
                return []
            except Exception as e:
                print(f"Error scraping Ashby {company_subdomain}: {e}")
                return []

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        print("Ashby: scrape_all_jobs not implemented - needs company list")
        return []

    def _parse_job(self, job: Dict, company: str) -> JobData:
        title = job.get("title") or job.get("jobTitle") or ""
        location = ""
        remote = False
        hybrid = False

        loc = job.get("location") or job.get("locationName") or ""
        if isinstance(loc, dict):
            location = loc.get("name") or loc.get("location") or ""
        else:
            location = str(loc or "")

        locations = job.get("locations") or []
        if not location and locations:
            first = locations[0]
            location = first.get("name", "") if isinstance(first, dict) else str(first)

        location_l = location.lower()
        remote = "remote" in location_l or bool(job.get("isRemote") or job.get("remote"))
        hybrid = "hybrid" in location_l

        external_id = str(job.get("id") or job.get("jobId") or job.get("jobPostingId") or "")
        external_url = (
            job.get("jobUrl")
            or job.get("applyUrl")
            or job.get("url")
            or f"https://jobs.ashbyhq.com/{company}/{external_id}"
        )
        description = job.get("descriptionHtml") or job.get("description") or job.get("descriptionPlain") or ""
        department = None
        dept = job.get("department") or job.get("team")
        if isinstance(dept, dict):
            department = dept.get("name")
        elif dept:
            department = str(dept)

        posted = None
        published = job.get("publishedAt") or job.get("publishedDate")
        if published:
            try:
                posted = datetime.fromisoformat(str(published).replace("Z", "+00:00"))
            except Exception:
                posted = None

        return JobData(
            title=title,
            company=company,
            location=location,
            external_id=external_id,
            external_url=external_url,
            description=description if isinstance(description, str) else str(description),
            remote=remote,
            hybrid=hybrid,
            department=department,
            seniority=self.parse_seniority(title),
            posted_date=posted,
            raw_data=job,
        )
