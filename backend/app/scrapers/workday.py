"""
Workday ATS Scraper

Workday powers career pages for most Fortune 500 companies (Salesforce, Amazon,
Netflix, Airbnb, etc.). The public job board API is at:
  https://{company}.wd1.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs

Returns JSON with job postings. No auth required.
"""

from typing import List, Dict, Optional
from datetime import datetime
import httpx

from .base import BaseScraper, JobData


class WorkdayScraper(BaseScraper):
    name = "workday"

    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        """Scrape jobs from a Workday career site.

        company_subdomain is the subdomain like:
          "salesforce.wd1.myworkdayjobs.com"
        """
        if company_subdomain.startswith("http"):
            company_subdomain = company_subdomain.replace("https://", "").replace("http://", "")

        # Extract tenant from subdomain (e.g. "salesforce" from "salesforce.wd1.myworkdayjobs.com")
        tenant = company_subdomain.split(".")[0]
        api_url = f"https://{company_subdomain}/wday/cxs/{tenant}/{tenant}/jobs"

        async with httpx.AsyncClient(
            headers={**self.headers, "Accept": "application/json", "Content-Type": "application/json"},
            timeout=30.0,
            follow_redirects=True,
        ) as client:
            try:
                payload = {"appliedFacets": {}, "limit": 50, "offset": 0, "searchText": ""}
                response = await client.post(api_url, json=payload)
                if response.status_code >= 400:
                    return []
                data = response.json()
                job_postings = data.get("jobPostings", [])
                print(f"  Workday: API returned {len(job_postings)} jobs for {tenant}")
                parsed = []
                for job in job_postings:
                    try:
                        parsed.append(self._parse_job(job, tenant))
                    except Exception as e:
                        print(f"  Workday: parse error: {e}")
                return parsed
            except Exception as e:
                print(f"  Workday: error scraping {company_subdomain}: {e}")
                return []

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        return []

    def _parse_job(self, job: Dict, company: str) -> JobData:
        title = job.get("title", "") or "Unknown Position"
        external_id = job.get("bulletin", "") or str(job.get("id", ""))
        external_url = f"https://{company}.wd1.myworkdayjobs.com/en-US/{company}/job/{external_id}"
        location = job.get("locationsText", "") or ""
        remote = "remote" in title.lower() or "remote" in location.lower()
        hybrid = "hybrid" in title.lower() or "hybrid" in location.lower()
        return JobData(
            title=title,
            company=company,
            location=location,
            external_id=external_id,
            external_url=external_url,
            description="",
            remote=remote,
            hybrid=hybrid,
            seniority=self.parse_seniority(title),
            posted_date=self._parse_date(job.get("postedOn")),
            raw_data=job,
        )

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
