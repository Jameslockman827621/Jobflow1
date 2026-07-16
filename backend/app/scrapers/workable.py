"""
Workable Scraper

Workable powers 100,000+ company career pages.
Public JSON endpoints:
- https://apply.workable.com/api/v1/widget/accounts/{slug}/jobs
- https://{slug}.workable.com/api/v2/jobs
"""

from typing import List, Dict, Any
import httpx

from .base import BaseScraper, JobData


class WorkableScraper(BaseScraper):
    name = "workable"
    base_url = "https://apply.workable.com/api/v1/widget/accounts"

    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        """Scrape jobs for a specific company via Workable JSON APIs."""
        slug = (company_subdomain or "").strip().lower()
        if not slug:
            return []

        urls = [
            f"https://apply.workable.com/api/v1/widget/accounts/{slug}/jobs",
            f"https://{slug}.workable.com/api/v2/jobs",
        ]

        proxies = None
        try:
            from app.services.proxy_pool import httpx_proxies
            proxies = httpx_proxies()
        except Exception:
            proxies = None

        async with httpx.AsyncClient(
            headers={**self.headers, "Accept": "application/json"},
            timeout=30.0,
            follow_redirects=True,
            proxies=proxies,
        ) as client:
            for url in urls:
                try:
                    response = await client.get(url)
                    if response.status_code != 200:
                        continue
                    data = response.json()
                    jobs_raw = self._extract_jobs(data)
                    if not jobs_raw:
                        continue
                    print(f"  Workable API returned {len(jobs_raw)} jobs for {slug} via {url}")
                    return [self._parse_job(job, slug) for job in jobs_raw if isinstance(job, dict)]
                except httpx.HTTPError as e:
                    print(f"HTTP error fetching Workable {url}: {e}")
                    continue
                except Exception as e:
                    print(f"Error parsing Workable response from {url}: {e}")
                    continue

        return []

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        """Workable doesn't have global search - needs company list"""
        print("Workable: scrape_all_jobs not implemented - needs company list")
        return []

    def _extract_jobs(self, data: Any) -> List[Dict]:
        if isinstance(data, list):
            return data
        if not isinstance(data, dict):
            return []
        jobs = data.get("jobs") or data.get("results") or data.get("data") or []
        return jobs if isinstance(jobs, list) else []

    def _format_location(self, location: Any) -> str:
        """Safely stringify Workable location (str or nested dict)."""
        if location is None:
            return ""
        if isinstance(location, str):
            return location
        if isinstance(location, dict):
            parts = []
            for key in ("city", "region", "state", "country", "location_str", "name", "telecommuting"):
                val = location.get(key)
                if val is True and key == "telecommuting":
                    parts.append("Remote")
                elif isinstance(val, str) and val.strip():
                    parts.append(val.strip())
            # Some payloads nest under "locations"
            if not parts and isinstance(location.get("locations"), list):
                return "; ".join(
                    self._format_location(loc) for loc in location["locations"] if loc
                )
            return ", ".join(parts)
        if isinstance(location, list):
            return "; ".join(self._format_location(loc) for loc in location if loc)
        return str(location)

    def _parse_job(self, job: Dict, company: str) -> JobData:
        """Parse Workable job data"""
        location = self._format_location(
            job.get("location") or job.get("locations") or job.get("city") or ""
        )
        loc_lower = location.lower()
        remote = bool(job.get("remote")) or "remote" in loc_lower or "telecommut" in loc_lower
        hybrid = bool(job.get("hybrid")) or "hybrid" in loc_lower

        external_id = job.get("id") or job.get("shortcode") or job.get("uid") or ""
        external_url = (
            job.get("url")
            or job.get("application_url")
            or job.get("shortlink")
            or ""
        )
        if not external_url and external_id:
            external_url = f"https://apply.workable.com/{company}/j/{external_id}/"

        description = job.get("description") or job.get("full_description") or ""
        if isinstance(description, dict):
            description = description.get("text") or description.get("html") or str(description)

        return JobData(
            title=job.get("title") or job.get("name") or "",
            company=company,
            location=location,
            external_id=str(external_id),
            external_url=external_url,
            description=description if isinstance(description, str) else str(description),
            remote=remote,
            hybrid=hybrid,
            department=job.get("department") or job.get("function"),
            seniority=self.parse_seniority(job.get("title") or job.get("name") or ""),
            raw_data=job,
        )
