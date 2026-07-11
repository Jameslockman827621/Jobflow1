"""
Ashby ATS Scraper

Ashby powers 2,000+ modern company career pages (Notion, Linear, Vercel, Retool, etc).
Public Job Board API (no auth):
  GET https://api.ashbyhq.com/posting-api/job-board/{job_board_name}?includeCompensation=true

The job_board_name is the final segment of the company's Ashby-hosted career page URL.
Example: https://jobs.ashbyhq.com/Ashby -> "Ashby"
"""

from typing import List, Dict, Optional
from datetime import datetime
import httpx

from .base import BaseScraper, JobData


class AshbyScraper(BaseScraper):
    name = "ashby"
    base_url = "https://api.ashbyhq.com/posting-api/job-board"

    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        """Scrape jobs for a specific company via Ashby public Job Board API."""
        # Ashby slugs are case-sensitive (e.g. "Ashby", "Linear", "Notion")
        # Try the provided slug, then a few capitalization variants.
        candidates = [
            company_subdomain,
            company_subdomain.capitalize(),
            company_subdomain.title(),
        ]
        # Deduplicate while preserving order
        seen = set()
        candidates = [c for c in candidates if not (c in seen or seen.add(c))]

        for slug in candidates:
            url = f"{self.base_url}/{slug}"
            params = {"includeCompensation": "true"}
            async with httpx.AsyncClient(
                headers=self.headers,
                timeout=30.0,
                follow_redirects=True,
            ) as client:
                try:
                    response = await client.get(url, params=params)
                    if response.status_code == 404:
                        continue
                    response.raise_for_status()
                    data = response.json()
                    jobs = data.get("jobs", []) or []
                    print(f"  Ashby: API returned {len(jobs)} jobs for {slug}")
                    parsed = []
                    for job in jobs:
                        try:
                            parsed.append(self._parse_job(job, slug))
                        except Exception as e:
                            print(f"  Ashby: parse error: {e}")
                    return parsed
                except httpx.HTTPError as e:
                    print(f"  Ashby: HTTP error for {slug}: {e}")
                    continue
                except Exception as e:
                    print(f"  Ashby: error scraping {slug}: {e}")
                    continue
        return []

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        """Scrape jobs across curated list of known Ashby companies."""
        from .companies import ASHBY_COMPANIES
        all_jobs: List[JobData] = []
        for company in ASHBY_COMPANIES[:limit]:
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
        """Search Ashby jobs across curated companies by keyword."""
        from .companies import ASHBY_COMPANIES
        results: List[JobData] = []
        kw = (keywords or "").lower()
        loc = (location or "").lower()
        for company in ASHBY_COMPANIES:
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
        """Parse Ashby Job Board API response."""
        title = job.get("title") or "Unknown Position"
        location = job.get("location") or ""
        # Ashby uses 'workplaceType' for remote/hybrid/office
        workplace = (job.get("workplaceType") or "").lower()
        remote = "remote" in workplace or "remote" in location.lower()
        hybrid = "hybrid" in workplace or "hybrid" in location.lower()

        # Department
        department = job.get("department") or job.get("departmentName")
        if isinstance(department, dict):
            department = department.get("name")

        # Compensation — Ashby returns structured comp when includeCompensation=true
        min_salary = None
        max_salary = None
        comp = job.get("compensation") or {}
        if isinstance(comp, dict):
            # Try scrapeableCompensationSalarySummary first (e.g. "$190K - $255K")
            summary = comp.get("scrapeableCompensationSalarySummary") or ""
            if summary:
                min_salary, max_salary = self.parse_salary(summary)
            if min_salary is None or max_salary is None:
                tier = comp.get("compensationTierSummary") or ""
                if tier:
                    t_min, t_max = self.parse_salary(tier)
                    if t_min and (min_salary is None or t_min < min_salary):
                        min_salary = t_min
                    if t_max and (max_salary is None or t_max > max_salary):
                        max_salary = t_max

        # Description — Ashby doesn't include full description in the public feed
        description = job.get("descriptionPlainText") or job.get("descriptionHtml") or ""

        # URLs
        job_url = job.get("jobUrl") or ""
        apply_url = job.get("applyUrl") or job_url

        # Employment type
        employment_type = job.get("employmentType") or job.get("employment") or None
        if employment_type:
            employment_type = self.parse_employment_type(str(employment_type)) or employment_type

        return JobData(
            title=title,
            company=company,
            location=location,
            external_id=str(job.get("id", "")),
            external_url=job_url,
            description=description,
            remote=remote,
            hybrid=hybrid,
            min_salary=min_salary,
            max_salary=max_salary,
            department=department,
            seniority=self.parse_seniority(title),
            employment_type=employment_type,
            posted_date=self._parse_date(job.get("postedDate") or job.get("createdAt")),
            raw_data=job,
        )

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            try:
                return datetime.utcfromtimestamp(int(value) / 1000)
            except (ValueError, TypeError, OSError):
                return None