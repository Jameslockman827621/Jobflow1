"""
Workday ATS Scraper

Workday powers career pages for most Fortune 500 companies (Salesforce, NVIDIA,
Visa, Workday itself, etc.). The public job board API is the Candidate Experience
Service (CXS) endpoint:

    POST https://{tenant}.{wd_server}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
    Body: {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""}

Three things you must get right (per the dev.to guide):
  1. `limit` cannot exceed 20 — Workday silently returns an empty array if you
     ask for more.
  2. It throttles fast paging — pause between requests or you'll silently lose jobs.
  3. The URL parts are not guessable — `tenant`, `wd_server` (wd1/wd3/wd5/...), and
     `site` (e.g. "External", "nvidiaExternalCareerSite") all come from the actual
     careers URL. Don't invent them.

This scraper accepts either:
  - A full careers URL: scrape_company_jobs("https://nvidia.wd5.myworkdayjobs.com/nvidiaExternalCareerSite")
  - A (tenant, wd_server, site) tuple: scrape_company_jobs(("nvidia", "wd5", "nvidiaExternalCareerSite"))
  - A bare tenant slug: scrape_company_jobs("nvidia") — looks it up in WORKDAY_COMPANIES

Returns JSON with job postings. No auth required.
"""

import re
from typing import List, Dict, Optional, Union, Tuple
from datetime import datetime
import asyncio

import httpx

from .base import BaseScraper, JobData


# Verified Workday tenants — each tuple is (tenant, wd_server, site).
# Verified against the live CXS API on 2026-07-11.
# Run scripts/discover_workday_companies.py to re-verify and find more.
WORKDAY_COMPANIES: List[Tuple[str, str, str]] = [
    # tenant, wd_server, site
    ("nvidia", "wd5", "nvidiaExternalCareerSite"),      # 2000 jobs
    ("visa", "wd5", "visa"),                            # 918 jobs
    ("uchicago", "wd5", "External"),                    # 397 jobs
    ("workday", "wd5", "workday"),                      # 369 jobs
    ("travelers", "wd5", "External"),                   # 352 jobs
    ("cmu", "wd5", "cmu"),                              # 193 jobs
]


URL_RE = re.compile(
    r"https?://([\w-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:en-[A-Za-z]{2}/)?([\w-]+)",
    re.IGNORECASE,
)


def _parse_url_or_slug(company_subdomain: str) -> Tuple[str, str, str]:
    """Parse a URL, tuple, or bare tenant slug into (tenant, wd_server, site)."""
    if isinstance(company_subdomain, (tuple, list)) and len(company_subdomain) >= 3:
        return (str(company_subdomain[0]), str(company_subdomain[1]), str(company_subdomain[2]))
    s = str(company_subdomain)
    # Full URL?
    m = URL_RE.search(s)
    if m:
        return (m.group(1), m.group(2), m.group(3))
    # Bare hostname like "nvidia.wd5.myworkdayjobs.com"
    m = re.match(r"^([\w-]+)\.(wd\d+)\.myworkdayjobs\.com", s, re.IGNORECASE)
    if m:
        tenant, wd = m.group(1), m.group(2)
        # Need to find the site — look it up in WORKDAY_COMPANIES
        for t, w, site in WORKDAY_COMPANIES:
            if t == tenant and w == wd:
                return (tenant, wd, site)
        # Fallback: try common site names
        return (tenant, wd, "External")
    # Bare tenant slug — look up in WORKDAY_COMPANIES
    for t, w, site in WORKDAY_COMPANIES:
        if t == s:
            return (t, w, site)
    # Last resort: assume wd5 and site=External
    return (s, "wd5", "External")


class WorkdayScraper(BaseScraper):
    name = "workday"

    async def scrape_company_jobs(
        self,
        company_subdomain: Union[str, Tuple[str, str, str]],
        max_jobs: int = 100,
    ) -> List[JobData]:
        """Scrape jobs from a Workday career site.

        Args:
            company_subdomain: full URL, (tenant, wd, site) tuple, or bare tenant slug.
            max_jobs: maximum jobs to fetch (paginated in chunks of 20).

        Returns:
            List of JobData.
        """
        tenant, wd, site = _parse_url_or_slug(company_subdomain)
        api_url = f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"

        async with httpx.AsyncClient(
            headers={
                **self.headers,
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=30.0,
            follow_redirects=True,
        ) as client:
            all_jobs: List[JobData] = []
            offset = 0
            # Workday caps limit at 20 — silently returns empty array above that.
            page_size = 20
            empty_pages = 0

            while offset < max_jobs:
                payload = {
                    "appliedFacets": {},
                    "limit": page_size,
                    "offset": offset,
                    "searchText": "",
                }
                try:
                    response = await client.post(api_url, json=payload)
                except Exception as e:
                    print(f"  Workday: error fetching {tenant} (offset={offset}): {e}")
                    break

                if response.status_code >= 400:
                    # 422 = wrong tenant/site combination
                    if response.status_code == 422 and offset == 0:
                        print(f"  Workday: 422 for {tenant}.{wd}/{site} — bad tenant/wd/site")
                    else:
                        print(f"  Workday: HTTP {response.status_code} for {tenant} (offset={offset})")
                    break

                try:
                    data = response.json()
                except Exception as e:
                    print(f"  Workday: JSON decode error for {tenant}: {e}")
                    break

                job_postings = data.get("jobPostings") or []
                total = int(data.get("total", 0))

                if offset == 0:
                    print(f"  Workday: {tenant}.{wd}/{site} — {total} total jobs")

                if not job_postings:
                    empty_pages += 1
                    if empty_pages >= 2:
                        # Two empty pages in a row — we're done (likely throttled)
                        break
                else:
                    empty_pages = 0

                for job in job_postings:
                    try:
                        all_jobs.append(self._parse_job(job, tenant, wd, site))
                    except Exception as e:
                        print(f"  Workday: parse error for job {job.get('id') or job.get('bulletin')}: {e}")

                offset += page_size
                if total and offset >= total:
                    break
                if len(job_postings) < page_size:
                    break

                # Polite pause between pages to avoid throttling
                await asyncio.sleep(0.3)

            return all_jobs

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        """Scrape jobs across all verified WORKDAY_COMPANIES."""
        all_jobs: List[JobData] = []
        for tenant, wd, site in WORKDAY_COMPANIES:
            try:
                jobs = await self.scrape_company_jobs((tenant, wd, site), max_jobs=limit)
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"  Workday: error scraping {tenant}: {e}")
                continue
        return all_jobs

    async def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        max_jobs: int = 50,
    ) -> List[JobData]:
        """Search Workday jobs across verified companies by keyword."""
        results: List[JobData] = []
        kw = (keywords or "").lower()
        loc = (location or "").lower()
        for tenant, wd, site in WORKDAY_COMPANIES:
            if len(results) >= max_jobs:
                break
            try:
                jobs = await self.scrape_company_jobs((tenant, wd, site), max_jobs=100)
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

    def _parse_job(self, job: Dict, tenant: str, wd: str, site: str) -> JobData:
        title = job.get("title", "") or "Unknown Position"
        external_id = job.get("bulletin", "") or str(job.get("id", ""))
        # externalPath typically looks like "/job/US-CA-Santa-Clara/Software-Engineer_JR026"
        # Build the apply URL: /en-US/{site}{external_path}
        external_path = job.get("externalPath") or external_id
        if not external_path.startswith("/"):
            external_path = "/" + external_path
        external_url = f"https://{tenant}.{wd}.myworkdayjobs.com/en-US/{site}{external_path}"
        location = job.get("locationsText", "") or ""
        if not location:
            # Fall back to primary location block
            locs = job.get("locations", []) or []
            if locs and isinstance(locs, list):
                first = locs[0]
                if isinstance(first, dict):
                    location = first.get("text", "") or ""
        remote = "remote" in title.lower() or "remote" in location.lower()
        hybrid = "hybrid" in title.lower() or "hybrid" in location.lower()
        company = tenant.replace("-", " ").title()
        # Date — postedOn is ISO 8601 with milliseconds
        posted_date = self._parse_date(job.get("postedOn"))
        return JobData(
            title=title,
            company=company,
            location=location,
            external_id=external_id,
            external_url=external_url,
            description="",  # Listing endpoint doesn't include description; would need a detail GET
            remote=remote,
            hybrid=hybrid,
            seniority=self.parse_seniority(title),
            posted_date=posted_date,
            raw_data=job,
        )

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        s = str(value).strip()
        if not s:
            return None
        # Workday uses ISO 8601 with milliseconds, e.g. "2024-08-15T12:34:56.000Z"
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            # Fall back to date-only
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
                try:
                    return datetime.strptime(s[:len(fmt) + 3], fmt)
                except ValueError:
                    continue
            return None
