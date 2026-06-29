"""
Remote-focused job board scrapers.

These boards have public RSS/JSON feeds that don't require auth or Apify:
  - RemoteOK:      https://remoteok.com/api
  - WeWorkRemotely: https://weworkremotely.com/remote-jobs.rss (RSS XML)
  - Remotive:       https://remotive.com/api/remote-jobs
  - Working Nomads: https://www.workingnomads.com/jobsapi
  - Himalayas:      https://himalayas.app/api/jobs

Used by the aggregator for keyword-based broad searches across the remote job market.
"""

from typing import List, Dict, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, JobData


class RemoteOKScraper(BaseScraper):
    """RemoteOK public JSON API."""

    name = "remoteok"
    base_url = "https://remoteok.com/api"

    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        # RemoteOK doesn't support per-company filtering
        return []

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        data = await self.fetch_json(self.base_url)
        if not data or not isinstance(data, list):
            return []
        # First item is a metadata object, skip it
        jobs = [item for item in data if isinstance(item, dict) and item.get("id")]
        results = []
        for job in jobs[:limit]:
            try:
                results.append(self._parse_job(job))
            except Exception:
                continue
        return results

    async def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        max_jobs: int = 50,
    ) -> List[JobData]:
        all_jobs = await self.scrape_all_jobs(limit=500)
        kw = (keywords or "").lower()
        results = []
        for j in all_jobs:
            if kw and kw not in (j.title or "").lower() and kw not in (j.description or "").lower():
                continue
            results.append(j)
            if len(results) >= max_jobs:
                break
        return results

    def _parse_job(self, job: Dict) -> JobData:
        title = job.get("position") or job.get("title") or "Unknown Position"
        company = job.get("company") or "Unknown"
        location = job.get("location") or "Remote"
        tags = job.get("tags") or []
        description = job.get("description") or ""
        # Salary (sometimes provided as a string like "$80k - $120k")
        min_salary, max_salary = self.parse_salary(job.get("salary") or "")
        return JobData(
            title=title,
            company=company,
            location=location,
            external_id=str(job.get("id", "")),
            external_url=job.get("url") or f"https://remoteok.com/l/{job.get('id', '')}",
            description=description,
            remote=True,
            hybrid=False,
            min_salary=min_salary,
            max_salary=max_salary,
            department=tags[0] if isinstance(tags, list) and tags else None,
            seniority=self.parse_seniority(title),
            employment_type=self.parse_employment_type(title),
            posted_date=self._parse_date(job.get("date")),
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


class WeWorkRemotelyScraper(BaseScraper):
    """WeWorkRemotely RSS feed."""

    name = "weworkremotely"
    base_url = "https://weworkremotely.com/remote-jobs.rss"

    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        return []

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        xml = await self.fetch(self.base_url)
        if not xml:
            return []
        return self._parse_rss(xml)[:limit]

    async def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        max_jobs: int = 50,
    ) -> List[JobData]:
        all_jobs = await self.scrape_all_jobs(limit=500)
        kw = (keywords or "").lower()
        results = []
        for j in all_jobs:
            if kw and kw not in (j.title or "").lower() and kw not in (j.description or "").lower():
                continue
            results.append(j)
            if len(results) >= max_jobs:
                break
        return results

    def _parse_rss(self, xml: str) -> List[JobData]:
        soup = BeautifulSoup(xml, "xml")
        items = soup.find_all("item")
        results = []
        for item in items:
            try:
                title_raw = item.find("title").get_text(strip=True) if item.find("title") else ""
                # WWR format: "Company: Job Title"
                company = ""
                title = title_raw
                if ":" in title_raw:
                    parts = title_raw.split(":", 1)
                    company = parts[0].strip()
                    title = parts[1].strip()
                link = item.find("link").get_text(strip=True) if item.find("link") else ""
                description = item.find("description").get_text(strip=True) if item.find("description") else ""
                pub_date = item.find("pubDate").get_text(strip=True) if item.find("pubDate") else ""
                categories = [c.get_text(strip=True) for c in item.find_all("category")]
                posted = None
                if pub_date:
                    try:
                        posted = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
                    except ValueError:
                        pass
                results.append(JobData(
                    title=title or "Unknown Position",
                    company=company,
                    location="Remote",
                    external_id=link or title_raw,
                    external_url=link,
                    description=description,
                    remote=True,
                    hybrid=False,
                    department=categories[0] if categories else None,
                    seniority=self.parse_seniority(title),
                    posted_date=posted,
                    raw_data={"title": title_raw, "categories": categories},
                ))
            except Exception:
                continue
        return results


class RemotiveScraper(BaseScraper):
    """Remotive public API."""

    name = "remotive"
    base_url = "https://remotive.com/api/remote-jobs"

    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        return []

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        data = await self.fetch_json(self.base_url)
        if not data or not isinstance(data, dict):
            return []
        jobs = data.get("jobs", []) or []
        results = []
        for job in jobs[:limit]:
            try:
                results.append(self._parse_job(job))
            except Exception:
                continue
        return results

    async def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        max_jobs: int = 50,
    ) -> List[JobData]:
        data = await self.fetch_json(self.base_url)
        if not data or not isinstance(data, dict):
            return []
        jobs = data.get("jobs", []) or []
        kw = (keywords or "").lower()
        results = []
        for job in jobs:
            title = job.get("title", "")
            if kw and kw not in title.lower() and kw not in (job.get("description") or "").lower():
                continue
            try:
                results.append(self._parse_job(job))
            except Exception:
                continue
            if len(results) >= max_jobs:
                break
        return results

    def _parse_job(self, job: Dict) -> JobData:
        title = job.get("title") or "Unknown Position"
        company = job.get("company_name") or "Unknown"
        location = job.get("candidate_required_location") or "Remote"
        return JobData(
            title=title,
            company=company,
            location=location,
            external_id=str(job.get("id", "")),
            external_url=job.get("url") or "",
            description=job.get("description") or "",
            remote=True,
            hybrid=False,
            department=job.get("category"),
            seniority=self.parse_seniority(title),
            employment_type=job.get("job_type"),
            posted_date=self._parse_date(job.get("publication_date")),
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


class HimalayasScraper(BaseScraper):
    """Himalayas public API."""

    name = "himalayas"
    base_url = "https://himalayas.app/jobs/api"

    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        return []

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        # Himalayas returns max 20 per request; paginate
        results = []
        offset = 0
        while len(results) < limit:
            data = await self.fetch_json(self.base_url, params={"limit": 20, "offset": offset})
            if not data or not isinstance(data, dict):
                break
            jobs = data.get("jobs", []) or []
            if not jobs:
                break
            for job in jobs:
                try:
                    results.append(self._parse_job(job))
                except Exception:
                    continue
            if len(jobs) < 20:
                break
            offset += 20
        return results[:limit]

    async def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        max_jobs: int = 50,
    ) -> List[JobData]:
        # Himalayas has a dedicated search endpoint
        url = f"{self.base_url}/search"
        params = {"page": 1}
        if keywords:
            params["q"] = keywords
        if location:
            params["country"] = location
        data = await self.fetch_json(url, params=params)
        if not data or not isinstance(data, dict):
            return []
        jobs = data.get("jobs", []) or data.get("results", []) or []
        results = []
        for job in jobs[:max_jobs]:
            try:
                results.append(self._parse_job(job))
            except Exception:
                continue
        return results

    def _parse_job(self, job: Dict) -> JobData:
        title = job.get("title") or "Unknown Position"
        company = job.get("companyName") or job.get("company") or "Unknown"
        # Location is an array of strings
        loc_arr = job.get("locationRestrictions") or []
        if isinstance(loc_arr, list) and loc_arr:
            location = ", ".join(str(l) for l in loc_arr)
        else:
            location = job.get("location") or "Remote"
        remote = True  # Himalayas is remote-only
        salary_min = job.get("minSalary")
        salary_max = job.get("maxSalary")
        # Seniority is an array
        seniority_arr = job.get("seniority") or []
        seniority = seniority_arr[0].lower().replace("-level", "").replace(" ", "") if seniority_arr else self.parse_seniority(title)
        return JobData(
            title=title,
            company=company,
            location=location,
            external_id=str(job.get("id") or job.get("slug") or ""),
            external_url=job.get("url") or f"https://himalayas.app/jobs/{job.get('slug', '')}",
            description=job.get("description") or job.get("excerpt") or "",
            remote=remote,
            hybrid=False,
            min_salary=int(salary_min) if salary_min else None,
            max_salary=int(salary_max) if salary_max else None,
            department=(job.get("categories") or [None])[0] if job.get("categories") else None,
            seniority=seniority,
            employment_type=job.get("employmentType"),
            posted_date=self._parse_date(job.get("postedAt") or job.get("publishedAt") or job.get("created_at")),
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