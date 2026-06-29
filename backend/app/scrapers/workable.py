"""
Workable ATS Scraper

Workable powers 100,000+ company career pages.
Public JSON API (no auth, browser-style request):
  https://{company}.workable.com/api/v3/jobs
Returns: { jobs: [...], total: N, ... }
"""

from typing import List, Dict, Optional
from datetime import datetime
import httpx

from .base import BaseScraper, JobData


class WorkableScraper(BaseScraper):
    name = "workable"
    base_url = "https://www.workable.com"

    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        """Scrape jobs for a specific company via Workable JSON API"""
        url = f"https://{company_subdomain}.workable.com/api/v3/jobs"

        # Workable requires browser-style headers — go directly to httpx so we can
        # inspect both text and json safely
        async with httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True,
        ) as client:
            try:
                response = await client.get(url)
                if response.status_code == 404:
                    return []
                response.raise_for_status()
                try:
                    data = response.json()
                except ValueError:
                    return []
                jobs = data.get("jobs", []) if isinstance(data, dict) else []
                print(f"  Workable: API returned {len(jobs)} jobs for {company_subdomain}")
                parsed = []
                for job in jobs:
                    try:
                        parsed.append(self._parse_job(job, company_subdomain))
                    except Exception as e:
                        print(f"  Workable: parse error: {e}")
                return parsed
            except httpx.HTTPError as e:
                print(f"  Workable: HTTP error for {company_subdomain}: {e}")
                return []

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        """Scrape jobs across curated list of known Workable companies"""
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
        """Search Workable jobs across curated companies by keyword"""
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
        """Parse Workable job data"""
        # Location can be a string or nested object
        location = ""
        loc_obj = job.get("location")
        if isinstance(loc_obj, dict):
            parts = [loc_obj.get("city"), loc_obj.get("region"), loc_obj.get("country")]
            location = ", ".join([p for p in parts if p])
        elif isinstance(loc_obj, str):
            location = loc_obj
        remote = job.get("remote") is True or "remote" in location.lower()
        hybrid = "hybrid" in location.lower()

        # Workable uses 'full_description' (HTML) and 'description' (plain)
        description = job.get("description") or job.get("full_description") or ""

        # Salary
        min_salary = None
        max_salary = None
        salary_obj = job.get("salary") or {}
        if isinstance(salary_obj, dict):
            try:
                if salary_obj.get("from"):
                    min_salary = int(float(salary_obj["from"]))
                if salary_obj.get("to"):
                    max_salary = int(float(salary_obj["to"]))
            except (ValueError, TypeError):
                pass

        return JobData(
            title=job.get("title") or "Unknown Position",
            company=job.get("company") or company,
            location=location,
            external_id=str(job.get("id", "")),
            external_url=job.get("url") or job.get("apply_url") or "",
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