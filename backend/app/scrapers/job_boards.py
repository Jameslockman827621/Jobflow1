"""
Job board scrapers for board-wide keyword search.

Sources:
  - Otta:        https://api.otta.com/api/jobs (POST search)
  - BuiltIn:     https://builtin.com/jobs (HTML scraping with JSON-LD)
  - Wellfound:   https://wellfound.com/jobs (HTML scraping with embedded JSON)

These require HTML parsing or JSON POST endpoints. The aggregator uses them
for broad searches across the modern tech job market.
"""

from typing import Any, List, Dict, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import json

from .base import BaseScraper, JobData


class OttaScraper(BaseScraper):
    """
    Otta job board scraper.

    Otta exposes a public JSON search endpoint used by their web UI:
      https://api.otta.com/api/jobs/search
    POST body: {"query": "...", "offset": 0, "limit": 50}

    Otta aggregates from many ATS providers and tags roles nicely.
    """

    name = "otta"
    base_url = "https://api.otta.com"

    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        return []

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        return await self.search_jobs(keywords="", max_jobs=limit)

    async def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        max_jobs: int = 50,
    ) -> List[JobData]:
        url = f"{self.base_url}/api/jobs/search"
        payload: Dict[str, Any] = {
            "query": keywords or "",
            "offset": 0,
            "limit": max_jobs,
        }
        if location:
            payload["location"] = location

        async with httpx.AsyncClient(
            headers={**self.headers, "Accept": "application/json", "Content-Type": "application/json"},
            timeout=20.0,
            follow_redirects=True,
        ) as client:
            try:
                response = await client.post(url, json=payload)
                if response.status_code >= 400:
                    return []
                data = response.json()
                jobs = data.get("jobs", []) or data.get("results", []) or []
                results = []
                for job in jobs[:max_jobs]:
                    try:
                        results.append(self._parse_job(job))
                    except Exception:
                        continue
                return results
            except (httpx.HTTPError, ValueError) as e:
                print(f"  Otta: error: {e}")
                return []

    def _parse_job(self, job: Dict) -> JobData:
        title = job.get("title") or job.get("name") or "Unknown Position"
        company_obj = job.get("company") or {}
        company = company_obj.get("name") if isinstance(company_obj, dict) else str(company_obj or "Unknown")
        location = job.get("location") or job.get("locations") or ""
        if isinstance(location, list):
            location = ", ".join(str(l) for l in location)
        return JobData(
            title=title,
            company=company,
            location=str(location),
            external_id=str(job.get("id", "")),
            external_url=job.get("url") or job.get("application_url") or "",
            description=job.get("description") or job.get("summary") or "",
            remote=job.get("remote") is True or "remote" in str(location).lower(),
            hybrid="hybrid" in str(location).lower(),
            department=job.get("department") or job.get("category"),
            seniority=self.parse_seniority(title),
            employment_type=job.get("employment_type") or job.get("job_type"),
            posted_date=self._parse_date(job.get("posted_at") or job.get("published_date")),
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


class WellfoundScraper(BaseScraper):
    """Wellfound (formerly AngelList Talent) — HTML scraping with embedded JSON."""

    name = "wellfound"
    base_url = "https://wellfound.com"

    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        return []

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        return await self.search_jobs(keywords="", max_jobs=limit)

    async def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        max_jobs: int = 50,
    ) -> List[JobData]:
        url = f"{self.base_url}/jobs"
        params = {"q": keywords or ""}
        if location:
            params["location"] = location
        html = await self.fetch(url, params=params)
        if not html:
            return []
        return self._parse_html(html)[:max_jobs]

    def _parse_html(self, html: str) -> List[JobData]:
        soup = BeautifulSoup(html, "lxml")
        results = []
        scripts = soup.find_all("script", type="application/json")
        for script in scripts:
            try:
                data = json.loads(script.string or "{}")
            except (ValueError, TypeError):
                continue
            jobs = self._extract_jobs_from_json(data)
            for job in jobs:
                try:
                    results.append(self._parse_job(job))
                except Exception:
                    continue
        return results

    def _extract_jobs_from_json(self, data: Any) -> List[Dict]:
        """Recursively find job objects in nested JSON."""
        if isinstance(data, dict):
            if "title" in data and ("company" in data or "startup" in data):
                return [data]
            jobs = []
            for v in data.values():
                jobs.extend(self._extract_jobs_from_json(v))
            return jobs
        if isinstance(data, list):
            jobs = []
            for item in data:
                jobs.extend(self._extract_jobs_from_json(item))
            return jobs
        return []

    def _parse_job(self, job: Dict) -> JobData:
        title = job.get("title") or "Unknown Position"
        company_obj = job.get("company") or job.get("startup") or {}
        company = company_obj.get("name") if isinstance(company_obj, dict) else str(company_obj or "Unknown")
        location = job.get("location") or job.get("remote") or ""
        if isinstance(location, dict):
            location = location.get("name") or str(location)
        remote = job.get("remote") is True or "remote" in str(location).lower()
        return JobData(
            title=title,
            company=company,
            location=str(location),
            external_id=str(job.get("id", "")),
            external_url=job.get("url") or f"https://wellfound.com/jobs/{job.get('id', '')}",
            description=job.get("description") or job.get("summary") or "",
            remote=remote,
            hybrid="hybrid" in str(location).lower(),
            seniority=self.parse_seniority(title),
            employment_type=job.get("job_type") or job.get("employment_type"),
            raw_data=job,
        )


class BuiltInScraper(BaseScraper):
    """BuiltIn — HTML scraping with JSON-LD JobPosting objects."""

    name = "builtin"
    base_url = "https://builtin.com"

    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        return []

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        return await self.search_jobs(keywords="", max_jobs=limit)

    async def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        max_jobs: int = 50,
    ) -> List[JobData]:
        url = f"{self.base_url}/jobs"
        params = {"q": keywords or ""}
        if location:
            params["location"] = location
        html = await self.fetch(url, params=params)
        if not html:
            return []
        return self._parse_html(html)[:max_jobs]

    def _parse_html(self, html: str) -> List[JobData]:
        soup = BeautifulSoup(html, "lxml")
        results = []
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string or "{}")
            except (ValueError, TypeError):
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                if item.get("@type") not in ("JobPosting", ["JobPosting"]):
                    continue
                try:
                    results.append(self._parse_jsonld(item))
                except Exception:
                    continue
        return results

    def _parse_jsonld(self, item: Dict) -> JobData:
        title = item.get("title") or "Unknown Position"
        org = item.get("hiringOrganization") or {}
        company = org.get("name") if isinstance(org, dict) else str(org or "Unknown")
        loc_obj = item.get("jobLocation") or {}
        if isinstance(loc_obj, dict):
            addr = loc_obj.get("address") or {}
            parts = [addr.get("addressLocality"), addr.get("addressRegion"), addr.get("addressCountry")]
            location = ", ".join([p for p in parts if p])
        else:
            location = str(loc_obj)
        return JobData(
            title=title,
            company=company,
            location=location,
            external_id=str(item.get("identifier") or item.get("@id") or ""),
            external_url=item.get("url") or "",
            description=item.get("description") or "",
            remote="remote" in location.lower(),
            hybrid="hybrid" in location.lower(),
            employment_type=item.get("employmentType"),
            posted_date=self._parse_date(item.get("datePosted")),
            raw_data=item,
        )

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None