"""
Ashby ATS Scraper

Ashby powers 2,000+ modern company career pages (Notion, Linear, Vercel, Retool, etc).
Ashby exposes a public GraphQL endpoint at:
  https://api.ashby.com/api/v1/get-postings

The endpoint accepts a JSON body with company subdomain and optional filters.
No auth required.
"""

from typing import List, Dict, Optional
from datetime import datetime
import httpx

from .base import BaseScraper, JobData


class AshbyScraper(BaseScraper):
    name = "ashby"
    base_url = "https://api.ashby.com"

    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        """Scrape jobs for a specific company via Ashby API"""
        url = f"{self.base_url}/api/v1/get-postings"
        payload = {
            "includeCompensation": True,
            "includeLocation": True,
            "includeReporting": True,
            "compensationRangeFilter": [],
            "locationFilter": [],
            "locationTypeFilter": [],
            "query": None,
            "searchSimilarity": 0.6,
            "departmentFilter": [],
            "employmentTypeFilter": [],
            "searchAfter": None,
            "sortBy": "postDate",
            "sortOrder": "desc",
            "subdomain": company_subdomain,
        }

        async with httpx.AsyncClient(
            headers={**self.headers, "Accept": "application/json", "Content-Type": "application/json"},
            timeout=30.0,
            follow_redirects=True,
        ) as client:
            try:
                response = await client.post(url, json=payload)
                if response.status_code == 404:
                    return []
                response.raise_for_status()
                data = response.json()
                if not data.get("success", True):
                    return []
                jobs = data.get("data", {}).get("postings", []) or []
                print(f"  Ashby: API returned {len(jobs)} jobs for {company_subdomain}")
                parsed = []
                for job in jobs:
                    try:
                        parsed.append(self._parse_job(job, company_subdomain))
                    except Exception as e:
                        print(f"  Ashby: parse error: {e}")
                return parsed
            except httpx.HTTPError as e:
                print(f"  Ashby: HTTP error for {company_subdomain}: {e}")
                return []

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        """Scrape jobs across curated list of known Ashby companies"""
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
        """Search Ashby jobs across curated companies by keyword"""
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
        """Parse Ashby job API response"""
        # Location
        location = ""
        loc_list = job.get("locationLocations") or []
        if isinstance(loc_list, list) and loc_list:
            first = loc_list[0]
            if isinstance(first, dict):
                city = first.get("city")
                region = first.get("region")
                country = first.get("country")
                parts = [p for p in [city, region, country] if p]
                location = ", ".join(parts)
        if not location:
            location = job.get("locationName") or job.get("location") or ""
        remote = (job.get("isRemote") is True) or "remote" in location.lower()
        hybrid = (job.get("isHybrid") is True) or "hybrid" in location.lower()

        # Department
        department = None
        dept_list = job.get("department") or []
        if isinstance(dept_list, list) and dept_list:
            first = dept_list[0]
            if isinstance(first, dict):
                department = first.get("name")

        # Compensation
        min_salary = None
        max_salary = None
        comp = job.get("compensation") or {}
        if isinstance(comp, dict):
            band = comp.get("band") or comp.get("range") or {}
            if isinstance(band, dict):
                try:
                    if band.get("minValue"):
                        min_salary = int(float(band["minValue"]))
                    if band.get("maxValue"):
                        max_salary = int(float(band["maxValue"]))
                except (ValueError, TypeError):
                    pass

        # Description — Ashby returns HTML in 'descriptionHtml'
        description = job.get("descriptionHtml") or job.get("descriptionPlainText") or job.get("description") or ""

        return JobData(
            title=job.get("title") or "Unknown Position",
            company=job.get("companyName") or company,
            location=location,
            external_id=str(job.get("id", "")),
            external_url=job.get("externalUrl") or job.get("url") or f"https://{company}.ashbyhq.com/{job.get('id', '')}",
            description=description,
            remote=remote,
            hybrid=hybrid,
            min_salary=min_salary,
            max_salary=max_salary,
            department=department,
            seniority=self.parse_seniority(job.get("title") or ""),
            employment_type=job.get("employmentType") or self.parse_employment_type(job.get("title") or ""),
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
                # Ashby sometimes returns epoch ms
                return datetime.utcfromtimestamp(int(value) / 1000)
            except (ValueError, TypeError, OSError):
                return None