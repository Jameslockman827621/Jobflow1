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
    Otta job board scraper (legacy).

    Otta was acquired by Welcome to the Jungle and now requires login (Google SSO).
    There is no public JSON API. This scraper is kept for compatibility but will
    return empty results. The aggregator marks it as unavailable in coverage.

    For curated tech jobs, the aggregator relies on Greenhouse/Ashby/Lever for
    company-specific roles and RemoteOK/WeWorkRemotely/Remotive/Himalayas for
    broad remote search.
    """

    name = "otta"
    base_url = "https://otta.com"

    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        return []

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        return []

    async def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        max_jobs: int = 50,
    ) -> List[JobData]:
        return []

    def _parse_job(self, job: Dict) -> JobData:
        return JobData(
            title=job.get("title", "Unknown"),
            company="Unknown",
            location="",
            external_id="",
            external_url="",
        )


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
        if not company:
            company = "Unknown"
        location = job.get("location") or job.get("remote") or ""
        if isinstance(location, dict):
            location = location.get("name") or str(location)
        # Don't stringify booleans — if location is a bool (remote flag), clear it
        if isinstance(location, bool):
            location = "Remote" if location else ""
        remote = job.get("remote") is True or "remote" in str(location).lower()
        return JobData(
            title=title,
            company=company,
            location=str(location) if location else "",
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
                # Direct JobPosting
                if item.get("@type") in ("JobPosting", ["JobPosting"]):
                    try:
                        results.append(self._parse_jsonld(item))
                    except Exception:
                        continue
                # ItemList — BuiltIn uses ListItem with name/url/description directly
                elif item.get("@type") == "ItemList":
                    for el in (item.get("itemListElement") or []):
                        if not isinstance(el, dict):
                            continue
                        # If ListItem has nested JobPosting item
                        inner = el.get("item") or el
                        if isinstance(inner, dict) and inner.get("@type") in ("JobPosting", ["JobPosting"]):
                            try:
                                results.append(self._parse_jsonld(inner))
                            except Exception:
                                continue
                        # BuiltIn-style ListItem with just name/url/description
                        elif el.get("@type") == "ListItem" and el.get("name") and el.get("url"):
                            try:
                                results.append(self._parse_listitem(el))
                            except Exception:
                                continue
                # @graph array
                elif "@graph" in item:
                    for g in item.get("@graph") or []:
                        if isinstance(g, dict):
                            if g.get("@type") in ("JobPosting", ["JobPosting"]):
                                try:
                                    results.append(self._parse_jsonld(g))
                                except Exception:
                                    continue
                            elif g.get("@type") == "ItemList":
                                for el in (g.get("itemListElement") or []):
                                    if not isinstance(el, dict):
                                        continue
                                    inner = el.get("item") or el
                                    if isinstance(inner, dict) and inner.get("@type") in ("JobPosting", ["JobPosting"]):
                                        try:
                                            results.append(self._parse_jsonld(inner))
                                        except Exception:
                                            continue
                                    elif el.get("@type") == "ListItem" and el.get("name") and el.get("url"):
                                        try:
                                            results.append(self._parse_listitem(el))
                                        except Exception:
                                            continue
        return results

    def _parse_listitem(self, el: Dict) -> JobData:
        """Parse BuiltIn-style ListItem with name/url/description."""
        title = el.get("name") or "Unknown Position"
        url = el.get("url") or ""
        description = el.get("description") or ""
        # BuiltIn URLs include the company in the path: /job/{title}/{id}
        # We can't reliably get the company from the ListItem alone — fetch the page
        # would be too slow, so we leave company as "Unknown" and the aggregator's
        # dedup will still work on URL.
        return JobData(
            title=title,
            company="Unknown",  # BuiltIn ListItem doesn't include company
            location="",  # BuiltIn ListItem doesn't include location
            external_id=url or f"builtin_{el.get('position', '')}",
            external_url=url,
            description=description,
            remote=False,
            hybrid=False,
            seniority=self.parse_seniority(title),
            raw_data=el,
        )

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