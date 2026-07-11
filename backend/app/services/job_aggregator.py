"""
Job Aggregator Service

Fans out a search across all available job sources in parallel:
  - ATS scrapers (Greenhouse, Lever, Workable, Ashby) for target companies
  - Job boards (LinkedIn, Indeed via Apify; Otta, Wellfound, BuiltIn)
  - Remote job boards (RemoteOK, WeWorkRemotely, Remotive, Himalayas)
  - Google Jobs as a meta-aggregator
  - Generic career page scraper for any user-supplied URLs

Each source runs in its own asyncio task with a timeout. Failures in one source
don't affect the others. Results are normalized to JobData dicts, deduplicated
across sources, and ranked by source priority (ATS > LinkedIn > Indeed > boards).

This is the "covers all angles" engine that powers on-demand search.
"""

import asyncio
import time
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime
from concurrent.futures import TimeoutError as AsyncTimeout

from app.core.config import settings
from app.scrapers.base import JobData
from app.scrapers.greenhouse import GreenhouseScraper
from app.scrapers.lever import LeverScraper
from app.scrapers.workable import WorkableScraper
from app.scrapers.ashby import AshbyScraper
from app.scrapers.workday import WorkdayScraper
from app.scrapers.google_jobs import GoogleJobsScraper
from app.scrapers.remote_boards import (
    RemoteOKScraper,
    WeWorkRemotelyScraper,
    RemotiveScraper,
    HimalayasScraper,
)
from app.scrapers.job_boards import (
    OttaScraper,
    WellfoundScraper,
    BuiltInScraper,
)
from app.scrapers.career_page import CareerPageScraper
from app.scrapers.companies import (
    COMPANY_DIRECTORY,
    get_company_atss,
    detect_ats_from_url,
    extract_company_slug,
)


# Source priority for deduplication (lower = higher priority)
SOURCE_PRIORITY = {
    "greenhouse": 0,
    "lever": 1,
    "ashby": 2,
    "workable": 3,
    "linkedin": 4,
    "indeed": 5,
    "otta": 6,
    "wellfound": 7,
    "builtin": 8,
    "remotive": 9,
    "weworkremotely": 10,
    "himalayas": 11,
    "remoteok": 12,
    "google_jobs": 13,
    "career_page": 14,
}

# Default per-source timeout (seconds)
DEFAULT_TIMEOUT = 25.0


class JobAggregator:
    """
    Aggregates jobs from multiple sources in parallel.

    Usage:
        aggregator = JobAggregator()
        results = await aggregator.search(
            keywords="Software Engineer",
            location="London",
            target_companies=["stripe", "monzo"],
            extra_career_urls=["https://example.com/careers"],
            remote_only=False,
            max_results=100,
        )
    """

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        self.timeout = timeout
        # ATS scrapers (per-company)
        self.greenhouse = GreenhouseScraper()
        self.lever = LeverScraper()
        self.workable = WorkableScraper()
        self.ashby = AshbyScraper()
        self.workday = WorkdayScraper()
        # Job board scrapers (keyword search)
        self.google_jobs = GoogleJobsScraper()
        self.otta = OttaScraper()
        self.wellfound = WellfoundScraper()
        self.builtin = BuiltInScraper()
        self.remoteok = RemoteOKScraper()
        self.weworkremotely = WeWorkRemotelyScraper()
        self.remotive = RemotiveScraper()
        self.himalayas = HimalayasScraper()
        # Generic
        self.career_page = CareerPageScraper()
        # Apify-powered scrapers (only if API key configured)
        self.linkedin_scraper = None
        self.indeed_scraper = None
        if settings.APIFY_API_KEY:
            try:
                from app.scrapers.apify_linkedin import ApifyLinkedInScraper
                from app.scrapers.apify_indeed import ApifyIndeedScraper
                self.linkedin_scraper = ApifyLinkedInScraper(api_key=settings.APIFY_API_KEY)
                self.indeed_scraper = ApifyIndeedScraper(api_key=settings.APIFY_API_KEY)
            except Exception as e:
                print(f"  Aggregator: Apify scrapers unavailable: {e}")

    async def search(
        self,
        keywords: str = "",
        location: Optional[str] = None,
        target_companies: Optional[List[str]] = None,
        extra_career_urls: Optional[List[str]] = None,
        remote_only: bool = False,
        employment_types: Optional[List[str]] = None,
        seniority_levels: Optional[List[str]] = None,
        max_results: int = 100,
        max_per_source: int = 50,
    ) -> Dict:
        """
        Run a search across all sources in parallel.

        Returns:
            {
                "jobs": List[Dict],         # deduplicated, ranked
                "total": int,
                "sources_used": Dict[str, int],
                "sources_failed": List[str],
                "duration_ms": int,
            }
        """
        start = time.time()
        target_companies = target_companies or []
        extra_career_urls = extra_career_urls or []

        # Build the list of (source_name, coroutine) pairs
        tasks: List[Tuple[str, asyncio.Task]] = []

        # 1. ATS scrapers for each target company (per-company)
        # For unknown companies, use the ATS discovery service to probe each ATS at runtime.
        for company in target_companies[:20]:
            ats_info = get_company_atss(company)
            if ats_info:
                tasks.append((
                    f"ats:{ats_info['ats']}:{company}",
                    asyncio.ensure_future(self._scrape_ats_company(ats_info["ats"], ats_info["slug"])),
                ))
            else:
                # Not in curated directory — use the ATS discovery service to find which ATS
                # this company uses at runtime. This works for any company on a supported ATS.
                async def _discover_and_scrape(name: str) -> List[JobData]:
                    try:
                        from app.services.ats_discovery import discover_company_ats
                        info = await discover_company_ats(name)
                        if not info:
                            return []
                        return await self._scrape_ats_company(info["ats"], info["slug"])
                    except Exception as e:
                        print(f"  Aggregator: discovery error for {name}: {e}")
                        return []
                tasks.append((f"discover:{company}", asyncio.ensure_future(_discover_and_scrape(company))))

        # 2. Keyword-search job boards (run in parallel)
        if keywords:
            tasks.append(("linkedin", asyncio.ensure_future(self._search_linkedin(keywords, location, remote_only, employment_types, max_per_source))))
            tasks.append(("indeed", asyncio.ensure_future(self._search_indeed(keywords, location, remote_only, employment_types, seniority_levels, max_per_source))))
            tasks.append(("otta", asyncio.ensure_future(self._safe(self.otta.search_jobs, keywords, location, max_per_source))))
            tasks.append(("wellfound", asyncio.ensure_future(self._safe(self.wellfound.search_jobs, keywords, location, max_per_source))))
            tasks.append(("builtin", asyncio.ensure_future(self._safe(self.builtin.search_jobs, keywords, location, max_per_source))))
            tasks.append(("remoteok", asyncio.ensure_future(self._safe(self.remoteok.search_jobs, keywords, None, max_per_source))))
            tasks.append(("weworkremotely", asyncio.ensure_future(self._safe(self.weworkremotely.search_jobs, keywords, None, max_per_source))))
            tasks.append(("remotive", asyncio.ensure_future(self._safe(self.remotive.search_jobs, keywords, None, max_per_source))))
            tasks.append(("himalayas", asyncio.ensure_future(self._safe(self.himalayas.search_jobs, keywords, location, max_per_source))))
            tasks.append(("google_jobs", asyncio.ensure_future(self._safe(self.google_jobs.search_jobs, keywords, location, remote_only, max_per_source))))

        # 3. Generic career page scraper for user-supplied URLs
        for url in extra_career_urls[:10]:
            ats = detect_ats_from_url(url)
            if ats:
                slug = extract_company_slug(url, ats)
                if slug:
                    tasks.append((f"ats:{ats}:{slug}", asyncio.ensure_future(self._scrape_ats_company(ats, slug))))
                    continue
            tasks.append((f"career_page:{url}", asyncio.ensure_future(self._safe(self.career_page.scrape_url, url))))

        if not tasks:
            return {"jobs": [], "total": 0, "sources_used": {}, "sources_failed": [], "duration_ms": 0}

        # Run all tasks with timeout, collect results as they complete
        results_by_source: Dict[str, List[JobData]] = {}
        sources_failed: List[str] = []

        async def run_one(name: str, task: asyncio.Task) -> Tuple[str, Optional[List[JobData]]]:
            try:
                result = await asyncio.wait_for(task, timeout=self.timeout)
                return name, result or []
            except asyncio.TimeoutError:
                print(f"  Aggregator: timeout for {name}")
                return name, None
            except Exception as e:
                print(f"  Aggregator: error in {name}: {e}")
                return name, None

        gathered = await asyncio.gather(*[run_one(name, task) for name, task in tasks])

        for name, result in gathered:
            if result is None:
                sources_failed.append(name)
            else:
                results_by_source[name] = result

        # Flatten and tag each job with its source
        all_jobs: List[Dict] = []
        sources_used: Dict[str, int] = {}
        for source_key, jobs in results_by_source.items():
            # source_key is like "ats:greenhouse:stripe" or "linkedin" or "career_page:https://..."
            source_name = self._extract_source_name(source_key)
            for j in jobs:
                d = j.to_dict()
                d["_source"] = source_name
                d["_source_key"] = source_key
                all_jobs.append(d)
            sources_used[source_name] = sources_used.get(source_name, 0) + len(jobs)

        # Deduplicate by URL (or company|title fallback)
        deduped = self._deduplicate(all_jobs)

        # Filter by preferences
        filtered = self._apply_filters(deduped, remote_only=remote_only, employment_types=employment_types, seniority_levels=seniority_levels)

        # Limit
        limited = filtered[:max_results]

        duration_ms = int((time.time() - start) * 1000)
        return {
            "jobs": limited,
            "total": len(limited),
            "sources_used": sources_used,
            "sources_failed": sources_failed,
            "duration_ms": duration_ms,
        }

    async def _scrape_ats_company(self, ats: str, slug: str) -> List[JobData]:
        """Scrape a specific ATS for a specific company slug.

        For Workday, the slug may be a bare tenant name — we look up the
        (tenant, wd_server, site) tuple in WORKDAY_COMPANIES, or fall back
        to a runtime probe.
        """
        if ats == "greenhouse":
            return await self.greenhouse.scrape_company_jobs(slug)
        if ats == "lever":
            return await self.lever.scrape_company_jobs(slug)
        if ats == "ashby":
            return await self.ashby.scrape_company_jobs(slug)
        if ats == "workable":
            return await self.workable.scrape_company_jobs(slug)
        if ats == "workday":
            # Look up the verified (tenant, wd, site) tuple
            from app.scrapers.workday import WORKDAY_COMPANIES, _parse_url_or_slug
            for tenant, wd, site in WORKDAY_COMPANIES:
                if tenant == slug:
                    return await self.workday.scrape_company_jobs((tenant, wd, site))
            # Fall back to URL/slug parsing — tries common patterns
            return await self.workday.scrape_company_jobs(slug)
        return []

    async def _search_linkedin(self, keywords: str, location: Optional[str], remote_only: bool, employment_types: Optional[List[str]], max_jobs: int) -> List[JobData]:
        if not self.linkedin_scraper:
            return []
        try:
            job_type = (employment_types or ["fulltime"])[0]
            remote = remote_only
            jobs = await self.linkedin_scraper.search_jobs(
                keywords=keywords,
                location=location or "United Kingdom",
                max_jobs=max_jobs,
                date_posted="month",
                job_type=job_type,
                remote=remote,
            )
            return jobs
        except Exception as e:
            print(f"  LinkedIn: error: {e}")
            return []

    async def _search_indeed(self, keywords: str, location: Optional[str], remote_only: bool, employment_types: Optional[List[str]], seniority_levels: Optional[List[str]], max_jobs: int) -> List[JobData]:
        if not self.indeed_scraper:
            return []
        try:
            job_type = (employment_types or ["fulltime"])[0]
            level = (seniority_levels or [""])[0]
            remote = "remote" if remote_only else None
            jobs = await self.indeed_scraper.search_jobs(
                query=keywords,
                location=(location or "London").split(",")[0].strip(),
                country="uk",
                max_jobs=max_jobs,
                remote=remote,
                job_type=job_type,
                from_days=14,
                sort="relevance",
            )
            return jobs
        except Exception as e:
            print(f"  Indeed: error: {e}")
            return []

    async def _safe(self, fn, *args, **kwargs) -> List[JobData]:
        """Wrap a coroutine function so exceptions don't bubble up."""
        try:
            result = await fn(*args, **kwargs)
            return result or []
        except Exception as e:
            print(f"  Aggregator: {fn.__name__} error: {e}")
            return []

    @staticmethod
    def _extract_source_name(source_key: str) -> str:
        if source_key.startswith("ats:"):
            return source_key.split(":")[1]
        if source_key.startswith("discover:"):
            # The actual ATS is discovered at runtime — extract from the results
            # For source counting purposes, we'll bucket these as "discovered"
            return "discovered"
        if source_key.startswith("career_page:"):
            return "career_page"
        return source_key

    @staticmethod
    def _deduplicate(jobs: List[Dict]) -> List[Dict]:
        """Deduplicate jobs by URL, then by company|title fallback."""
        seen_urls: Set[str] = set()
        seen_keys: Set[str] = set()
        deduped: List[Dict] = []

        # Sort by source priority so preferred sources win on duplicates
        jobs_sorted = sorted(
            jobs,
            key=lambda j: SOURCE_PRIORITY.get(j.get("_source", ""), 99),
        )

        for job in jobs_sorted:
            url = (job.get("external_url") or "").strip()
            title = (job.get("title") or "").strip().lower()
            company = (job.get("company") or "").strip().lower()

            if url:
                # Normalize URL for comparison
                norm = url.rstrip("/").split("?")[0].lower()
                if norm in seen_urls:
                    continue
                seen_urls.add(norm)
            else:
                key = f"{company}|{title}"
                if key in seen_keys:
                    continue
                seen_keys.add(key)

            deduped.append(job)
        return deduped

    @staticmethod
    def _apply_filters(
        jobs: List[Dict],
        remote_only: bool = False,
        employment_types: Optional[List[str]] = None,
        seniority_levels: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Apply user preference filters to a list of job dicts."""
        filtered = []
        types_norm = [t.lower().replace("-", "").replace("_", "") for t in (employment_types or [])]
        levels_norm = [l.lower() for l in (seniority_levels or [])]

        for job in jobs:
            if remote_only and not job.get("remote"):
                continue
            if types_norm:
                et = (job.get("employment_type") or "").lower().replace("-", "").replace("_", "").replace(" ", "")
                if et and et not in types_norm:
                    # Some sources use "FULL_TIME" — check both forms
                    if not any(t in et for t in types_norm):
                        continue
            if levels_norm:
                sen = (job.get("seniority") or "").lower()
                if sen and sen not in levels_norm:
                    # Allow some flexibility: 'mid_level' matches 'mid'
                    if not any(l in sen or sen in l for l in levels_norm):
                        continue
            filtered.append(job)
        return filtered

    def list_available_sources(self) -> List[Dict]:
        """Return metadata about all available sources (used by frontend coverage UI)."""
        sources = [
            {"id": "greenhouse", "name": "Greenhouse", "type": "ats", "needs_api_key": False, "coverage": "40,000+ companies"},
            {"id": "lever", "name": "Lever", "type": "ats", "needs_api_key": False, "coverage": "10,000+ companies"},
            {"id": "ashby", "name": "Ashby", "type": "ats", "needs_api_key": False, "coverage": "2,000+ modern startups"},
            {"id": "workable", "name": "Workable", "type": "ats", "needs_api_key": False, "coverage": "100,000+ companies"},
            {"id": "workday", "name": "Workday", "type": "ats", "needs_api_key": False, "coverage": "Fortune 500 + enterprise"},
            {"id": "linkedin", "name": "LinkedIn", "type": "board", "needs_api_key": True, "coverage": "Global professional network"},
            {"id": "indeed", "name": "Indeed", "type": "board", "needs_api_key": True, "coverage": "Largest job board globally"},
            {"id": "otta", "name": "Otta (now Welcome to the Jungle)", "type": "board", "needs_api_key": False, "requires_auth": True, "coverage": "Now requires login — disabled"},
            {"id": "wellfound", "name": "Wellfound (AngelList)", "type": "board", "needs_api_key": False, "requires_auth": True, "coverage": "Requires login — disabled"},
            {"id": "builtin", "name": "BuiltIn", "type": "board", "needs_api_key": False, "coverage": "Tech hubs (NYC, SF, etc.)"},
            {"id": "remoteok", "name": "RemoteOK", "type": "remote_board", "needs_api_key": False, "coverage": "Remote jobs"},
            {"id": "weworkremotely", "name": "WeWorkRemotely", "type": "remote_board", "needs_api_key": False, "coverage": "Remote jobs (largest)"},
            {"id": "remotive", "name": "Remotive", "type": "remote_board", "needs_api_key": False, "coverage": "Remote jobs"},
            {"id": "himalayas", "name": "Himalayas", "type": "remote_board", "needs_api_key": False, "coverage": "Remote jobs (search API)"},
            {"id": "google_jobs", "name": "Google Jobs", "type": "meta", "needs_api_key": False, "coverage": "Aggregates from many sources"},
            {"id": "career_page", "name": "Direct Career Pages", "type": "generic", "needs_api_key": False, "coverage": "Any company career URL via JSON-LD"},
        ]
        for s in sources:
            # Sources requiring auth are unavailable
            if s.get("requires_auth"):
                s["available"] = False
                s["note"] = "Requires login — not scrapable without auth"
                continue
            # Sources needing Apify key
            if s.get("needs_api_key") and not settings.APIFY_API_KEY:
                s["available"] = False
                s["note"] = "Requires APIFY_API_KEY"
                continue
            s["available"] = True
        return sources


# Convenience module-level instance for reuse
_aggregator: Optional[JobAggregator] = None


def get_aggregator() -> JobAggregator:
    global _aggregator
    if _aggregator is None:
        _aggregator = JobAggregator()
    return _aggregator