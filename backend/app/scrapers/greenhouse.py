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
        # Greenhouse supports two board URL formats:
        #  - boards-api.greenhouse.io/v1/boards/{company}/jobs
        #  - boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true
        url = f"{self.base_url}/{company_subdomain}/jobs"
        params = {"content": "true"}

        async with httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True,
        ) as client:
            try:
                response = await client.get(url, params=params)
                if response.status_code == 404:
                    return []
                response.raise_for_status()
                data = response.json()
                jobs = data.get("jobs", [])
                print(f"  Greenhouse: API returned {len(jobs)} jobs for {company_subdomain}")
                parsed = []
                for job in jobs:
                    try:
                        parsed.append(self._parse_job(job, company_subdomain))
                    except Exception as e:
                        print(f"  Greenhouse: parse error for job {job.get('id')}: {e}")
                return parsed
            except httpx.HTTPStatusError as e:
                print(f"  Greenhouse: HTTP error for {company_subdomain}: {e.response.status_code}")
                return []
            except Exception as e:
                print(f"  Greenhouse: error scraping {company_subdomain}: {e}")
                return []

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        """Scrape jobs across curated list of known Greenhouse companies"""
        from .companies import GREENHOUSE_COMPANIES
        all_jobs: List[JobData] = []
        for company in GREENHOUSE_COMPANIES[:limit]:
            try:
                jobs = await self.scrape_company_jobs(company)
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"  Greenhouse: error for {company}: {e}")
                continue
        return all_jobs

    async def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        max_jobs: int = 50,
    ) -> List[JobData]:
        """Search Greenhouse jobs across curated companies by keyword"""
        from .companies import GREENHOUSE_COMPANIES
        results: List[JobData] = []
        kw = (keywords or "").lower()
        loc = (location or "").lower()
        for company in GREENHOUSE_COMPANIES:
            if len(results) >= max_jobs:
                break
            try:
                jobs = await self.scrape_company_jobs(company)
                for j in jobs:
                    if kw and kw not in (j.title or "").lower() and kw not in (j.description or "").lower():
                        continue
                    if loc and loc not in (j.location or "").lower():
                        continue
                    results.append(j)
                    if len(results) >= max_jobs:
                        break
            except Exception:
                continue
        return results

    def _parse_job(self, job: Dict, company: str) -> JobData:
        """Parse Greenhouse job API response"""
        location = ""
        remote = False
        hybrid = False

        # Parse locations — Greenhouse returns either a list of location objects
        # or a single location string
        locations = job.get("locations", [])
        if isinstance(locations, list) and locations:
            first = locations[0]
            if isinstance(first, dict):
                location = first.get("name", "") or ""
            else:
                location = str(first)
            remote = "remote" in location.lower()
            hybrid = "hybrid" in location.lower()
        elif isinstance(locations, str):
            location = locations
            remote = "remote" in location.lower()
            hybrid = "hybrid" in location.lower()

        # Some boards use location->name structure
        if not location:
            loc_obj = job.get("location", {})
            if isinstance(loc_obj, dict):
                location = loc_obj.get("name", "") or ""

        # Parse departments
        departments = job.get("departments", [])
        department = None
        if isinstance(departments, list) and departments:
            first = departments[0]
            if isinstance(first, dict):
                department = first.get("name")

        # Parse seniority from title
        seniority = self.parse_seniority(job.get("title", ""))

        # Parse description - Greenhouse returns it as HTML
        description_obj = job.get("description", {})
        description = ""
        if isinstance(description_obj, dict):
            description = description_obj.get("content", "") or description_obj.get("text", "")
        elif isinstance(description_obj, str):
            description = description_obj

        # Metadata for employment type / remote
        metadata = job.get("metadata", []) or []
        employment_type = None
        for m in metadata:
            if not isinstance(m, dict):
                continue
            field_name = (m.get("name") or "").lower()
            value = m.get("value") or ""
            if "employment" in field_name or "type" in field_name:
                employment_type = self.parse_employment_type(str(value))
            if "remote" in field_name and "remote" in str(value).lower():
                remote = True
            if "hybrid" in field_name and "hybrid" in str(value).lower():
                hybrid = True

        return JobData(
            title=job.get("title", "") or "Unknown Position",
            company=company,
            location=location,
            external_id=str(job.get("id", "")),
            external_url=job.get("absolute_url", "") or "",
            description=description,
            remote=remote,
            hybrid=hybrid,
            min_salary=None,
            max_salary=None,
            department=department,
            seniority=seniority,
            employment_type=employment_type,
            posted_date=self._parse_date(job.get("updated_at")) or self._parse_date(job.get("first_published")),
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
