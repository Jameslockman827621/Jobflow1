"""
Workable ATS Scraper

Workable powers 100,000+ company career pages.
Public read-only endpoint (no auth):
  GET https://www.workable.com/api/accounts/{subdomain}?details=true

Returns published jobs plus job details from the public careers layer.
Companion endpoints return locations and departments:
  GET https://www.workable.com/api/accounts/{subdomain}/locations
  GET https://www.workable.com/api/accounts/{subdomain}/departments
"""

from typing import List, Dict, Optional
from datetime import datetime
import httpx

from .base import BaseScraper, JobData


class WorkableScraper(BaseScraper):
    name = "workable"
    base_url = "https://www.workable.com/api/accounts"

    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        """Scrape jobs for a specific company via Workable public API."""
        slug = company_subdomain.lower().replace(" ", "-")
        url = f"{self.base_url}/{slug}"
        params = {"details": "true"}

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
                try:
                    data = response.json()
                except ValueError:
                    return []
                # Workable returns either a list of jobs directly or {jobs: [...]}
                if isinstance(data, list):
                    jobs = data
                elif isinstance(data, dict):
                    jobs = data.get("jobs", []) or []
                    # Some responses nest jobs under 'result'
                    if not jobs and isinstance(data.get("result"), list):
                        jobs = data["result"]
                else:
                    jobs = []
                print(f"  Workable: API returned {len(jobs)} jobs for {slug}")
                parsed = []
                for job in jobs:
                    try:
                        parsed.append(self._parse_job(job, slug))
                    except Exception as e:
                        print(f"  Workable: parse error: {e}")
                return parsed
            except httpx.HTTPError as e:
                print(f"  Workable: HTTP error for {slug}: {e}")
                return []

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        """Scrape jobs across curated list of known Workable companies."""
        from .companies import WORKABLE_COMPANIES
        all_jobs: List[JobData] = []
        for company in WORKABLE_COMPANIES[:limit]:
            try:
                jobs = await self.scrape_company_jobs(company)
                all_jobs.extend(jobs)
            except Exception:
                continue
        return all_jobs

    async def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        max_jobs: int = 50,
    ) -> List[JobData]:
        """Search Workable jobs across curated companies by keyword."""
        from .companies import WORKABLE_COMPANIES
        results: List[JobData] = []
        kw = (keywords or "").lower()
        loc = (location or "").lower()
        for company in WORKABLE_COMPANIES:
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
        """Parse Workable job data."""
        # Location can be a string, nested object, or null
        location = ""
        loc_obj = job.get("location")
        if isinstance(loc_obj, dict):
            parts = [loc_obj.get("city"), loc_obj.get("region"), loc_obj.get("country")]
            location = ", ".join([p for p in parts if p])
        elif isinstance(loc_obj, str):
            location = loc_obj
        # Workable also has 'location_str' field
        if not location and job.get("location_str"):
            location = job["location_str"]
        remote = job.get("remote") is True or "remote" in location.lower()
        hybrid = "hybrid" in location.lower()

        # Workable uses 'description' (plain) and 'full_description' (HTML)
        description = job.get("full_description") or job.get("description") or ""

        # Salary
        min_salary = None
        max_salary = None
        salary_obj = job.get("salary") or {}
        if isinstance(salary_obj, dict):
            try:
                if salary_obj.get("salary_from") or salary_obj.get("from"):
                    min_salary = int(float(salary_obj.get("salary_from") or salary_obj.get("from")))
                if salary_obj.get("salary_to") or salary_obj.get("to"):
                    max_salary = int(float(salary_obj.get("salary_to") or salary_obj.get("to")))
            except (ValueError, TypeError):
                pass

        # URLs
        url = job.get("url") or job.get("apply_url") or ""
        if not url and job.get("shortcode"):
            url = f"https://apply.workable.com/j/{job['shortcode']}"

        return JobData(
            title=job.get("title") or "Unknown Position",
            company=job.get("company") or company,
            location=location,
            external_id=str(job.get("id") or job.get("shortcode") or ""),
            external_url=url,
            description=description,
            remote=remote,
            hybrid=hybrid,
            min_salary=min_salary,
            max_salary=max_salary,
            department=job.get("department"),
            seniority=self.parse_seniority(job.get("title") or ""),
            employment_type=job.get("employment_type") or self.parse_employment_type(job.get("title") or ""),
            posted_date=self._parse_date(job.get("published_on") or job.get("created_at")),
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