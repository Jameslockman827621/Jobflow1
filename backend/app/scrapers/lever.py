"""
Lever ATS Scraper

Lever powers 10,000+ company career pages.
Lever exposes a public JSON API at:
  https://api.lever.co/v0/postings/{company}?mode=json
HTML scraping is fragile; the JSON endpoint is the supported approach.
"""

from typing import List, Dict, Optional
from datetime import datetime
import httpx

from .base import BaseScraper, JobData


class LeverScraper(BaseScraper):
    name = "lever"
    base_url = "https://api.lever.co/v0/postings"

    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        """Scrape jobs for a specific company via Lever JSON API"""
        url = f"{self.base_url}/{company_subdomain}"
        params = {"mode": "json"}

        async with httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True,
        ) as client:
            try:
                response = await client.get(url, params=params)
                if response.status_code == 404:
                    print(f"  Lever: {company_subdomain} not on Lever")
                    return []
                response.raise_for_status()
                data = response.json()
                # Lever returns either a list (postings) or {postings: [...]}
                if isinstance(data, list):
                    jobs = data
                elif isinstance(data, dict):
                    jobs = data.get("postings", [])
                else:
                    jobs = []
                print(f"  Lever: API returned {len(jobs)} jobs for {company_subdomain}")
                parsed = []
                for job in jobs:
                    try:
                        parsed.append(self._parse_job(job, company_subdomain))
                    except Exception as e:
                        print(f"  Lever: parse error for job {job.get('id')}: {e}")
                return parsed
            except httpx.HTTPStatusError as e:
                print(f"  Lever: HTTP error for {company_subdomain}: {e.response.status_code}")
                return []
            except Exception as e:
                print(f"  Lever: error scraping {company_subdomain}: {e}")
                return []

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        """Scrape jobs across curated list of known Lever companies"""
        from .companies import LEVER_COMPANIES
        all_jobs: List[JobData] = []
        for company in LEVER_COMPANIES[:limit]:
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
        """Search Lever jobs across curated companies by keyword"""
        from .companies import LEVER_COMPANIES
        results: List[JobData] = []
        kw = (keywords or "").lower()
        loc = (location or "").lower()
        for company in LEVER_COMPANIES:
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
        """Parse Lever job API response"""
        # Lever uses 'text' (full HTML) and 'descriptionPlain' (plain text)
        description = job.get("descriptionPlain") or job.get("description") or ""

        # Location — Lever uses nested 'regions' list and 'country'
        location = ""
        regions = job.get("regions") or []
        if isinstance(regions, list) and regions:
            location = ", ".join(str(r) for r in regions if r)
        else:
            country = job.get("country")
            if country:
                location = country if isinstance(country, str) else str(country)
            city = job.get("city")
            if city:
                location = f"{city}, {location}" if location else str(city)

        remote = "remote" in location.lower() or job.get("workplaceType", "").lower() == "remote"
        hybrid = "hybrid" in location.lower() or job.get("workplaceType", "").lower() == "hybrid"

        # Department / team
        departments = job.get("tags") or []
        department = None
        if isinstance(departments, list):
            for tag in departments:
                if isinstance(tag, dict) and tag.get("type") == "team":
                    department = tag.get("name")
                    break

        # Salary (Lever rarely exposes, but check 'salaryRange' if present)
        min_salary = None
        max_salary = None
        salary_range = job.get("salaryRange")
        if isinstance(salary_range, dict):
            min_val = salary_range.get("min")
            max_val = salary_range.get("max")
            try:
                if min_val is not None:
                    min_salary = int(float(min_val))
                if max_val is not None:
                    max_salary = int(float(max_val))
            except (ValueError, TypeError):
                pass

        return JobData(
            title=job.get("text") or job.get("title") or "Unknown Position",
            company=job.get("companyName") or company,
            location=location,
            external_id=str(job.get("id", "")),
            external_url=job.get("hostedUrl") or job.get("applyUrl") or "",
            description=description,
            remote=remote,
            hybrid=hybrid,
            min_salary=min_salary,
            max_salary=max_salary,
            department=department,
            seniority=self.parse_seniority(job.get("text") or job.get("title") or ""),
            employment_type=self.parse_employment_type(job.get("commitment") or ""),
            posted_date=self._parse_date(job.get("createdAt")),
            raw_data=job,
        )

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[datetime]:
        if value is None or value == "":
            return None
        # Lever sometimes returns createdAt as an epoch millis integer
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(int(value) / 1000.0)
            except (ValueError, OSError, OverflowError):
                return None
        s = str(value).strip()
        if not s:
            return None
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None