"""ATS Discovery Service

Given a company name, probes each supported ATS (Greenhouse, Lever, Ashby,
Workable, Workday) with multiple slug variations to find which ATS the company
uses and what their slug/site is. This lets JobScale work for ANY company that
uses a supported ATS — not just the ones in our curated COMPANY_DIRECTORY.

The discovery is cached in-memory for the process lifetime so repeated searches
for the same company are fast.

Usage:
    from app.services.ats_discovery import discover_company_ats
    result = await discover_company_ats("acme corp")
    # result = {"ats": "greenhouse", "slug": "acmecorp", "jobs": 42}
    # result = None if no ATS found
"""

import asyncio
import re
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

import httpx


# Slug variations to try for a given company name.
# "Acme Corp" -> ["acme", "acmecorp", "acme-corp", "acme_corp", "acmecorporation"]
def _slug_variations(name: str) -> List[str]:
    if not name:
        return []
    s = name.lower().strip()
    # Strip common suffixes
    for suffix in (", inc.", ", inc", " inc.", " inc", " corp.", " corp",
                   " corporation", " co.", " co", " ltd.", " ltd", " limited",
                   " llc", " gmbh", " sa", " ag", " pty", " pty ltd"):
        if s.endswith(suffix):
            s = s[: -len(suffix)].strip()
    # Replace separators
    base = re.sub(r"[^a-z0-9]+", "", s)  # acmecorp
    hyphen = re.sub(r"[^a-z0-9]+", "-", s).strip("-")  # acme-corp
    underscore = re.sub(r"[^a-z0-9]+", "_", s).strip("_")  # acme_corp
    out = []
    for v in (base, hyphen, underscore, s.replace(" ", "")):
        if v and v not in out:
            out.append(v)
    # Common short forms
    if " " in s:
        first = s.split()[0]
        if first not in out:
            out.append(first)
    return out


async def _probe_greenhouse(client: httpx.AsyncClient, slug: str) -> Optional[int]:
    try:
        r = await client.get(
            f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
            headers={"Accept": "application/json"},
        )
        if r.status_code == 200:
            data = r.json()
            jobs = data.get("jobs", [])
            if jobs:
                return len(jobs)
            # 200 with no jobs — still a valid board, just empty
            return 0
    except Exception:
        pass
    return None


async def _probe_lever(client: httpx.AsyncClient, slug: str) -> Optional[int]:
    try:
        r = await client.get(
            f"https://api.lever.co/v0/postings/{slug}",
            params={"mode": "json"},
            headers={"Accept": "application/json"},
        )
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                return len(data)
            if isinstance(data, dict):
                return len(data.get("postings", []))
    except Exception:
        pass
    return None


async def _probe_ashby(client: httpx.AsyncClient, slug: str) -> Optional[int]:
    # Ashby uses POST with a JSON body — the slug is the "configuredAtsUrl"
    try:
        r = await client.post(
            "https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true".format(slug=slug),
            json={},
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                return len(data)
            if isinstance(data, dict):
                return len(data.get("postings", []))
    except Exception:
        pass
    return None


async def _probe_workable(client: httpx.AsyncClient, slug: str) -> Optional[int]:
    try:
        r = await client.get(
            f"https://www.workable.com/api/accounts/{slug}?details=true",
            headers={"Accept": "application/json"},
        )
        if r.status_code == 200:
            data = r.json()
            return len(data.get("jobs", []))
    except Exception:
        pass
    return None


async def _probe_workday(
    client: httpx.AsyncClient, tenant: str, wd: str, site: str
) -> Optional[int]:
    try:
        r = await client.post(
            f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs",
            json={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""},
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        if r.status_code == 200:
            data = r.json()
            return int(data.get("total", 0))
    except Exception:
        pass
    return None


async def _probe_one_ats(
    client: httpx.AsyncClient, ats: str, slug: str
) -> Optional[Tuple[str, int, Optional[Dict]]]:
    """Probe one (ats, slug) combination. Returns (ats, job_count, extra_metadata) or None."""
    if ats == "greenhouse":
        n = await _probe_greenhouse(client, slug)
        if n is not None:
            return (ats, n, {"slug": slug})
    elif ats == "lever":
        n = await _probe_lever(client, slug)
        if n is not None:
            return (ats, n, {"slug": slug})
    elif ats == "ashby":
        n = await _probe_ashby(client, slug)
        if n is not None:
            return (ats, n, {"slug": slug})
    elif ats == "workable":
        n = await _probe_workable(client, slug)
        if n is not None:
            return (ats, n, {"slug": slug})
    elif ats == "workday":
        # Workday needs (tenant, wd, site). Try common patterns.
        for wd in ("wd5", "wd3", "wd1"):
            for site_template in (
                lambda t: t,
                lambda t: f"{t}ExternalCareerSite",
                lambda t: f"{t.capitalize()}ExternalCareerSite",
                lambda t: "External",
                lambda t: "ExternalCareerSite",
            ):
                site = site_template(slug)
                n = await _probe_workday(client, slug, wd, site)
                if n is not None and n > 0:
                    return (ats, n, {"slug": slug, "wd": wd, "site": site})
    return None


# In-process cache so repeated discoveries don't re-probe
_DISCOVERY_CACHE: Dict[str, Optional[Dict]] = {}


async def discover_company_ats(name: str, timeout: float = 10.0) -> Optional[Dict]:
    """Discover which ATS a company uses by probing each supported ATS.

    Args:
        name: Company name (e.g., "Acme Corp", "Stripe", "NVIDIA").
        timeout: Per-request timeout in seconds.

    Returns:
        Dict with keys: ats, slug, jobs, plus extra metadata (e.g., wd, site for Workday).
        None if no ATS found.

    Cached in-process for the lifetime of the worker.
    """
    if not name:
        return None
    cache_key = name.lower().strip()
    if cache_key in _DISCOVERY_CACHE:
        return _DISCOVERY_CACHE[cache_key]

    # Check the curated directory first — fast path
    from app.scrapers.companies import get_company_atss
    curated = get_company_atss(name)
    if curated:
        result = {
            "ats": curated["ats"],
            "slug": curated["slug"],
            "jobs": None,  # unknown until we probe
            "name": curated["name"],
        }
        _DISCOVERY_CACHE[cache_key] = result
        return result

    slugs = _slug_variations(name)
    if not slugs:
        _DISCOVERY_CACHE[cache_key] = None
        return None

    # Probe each ATS with each slug variation in parallel
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        probes = []
        for ats in ("greenhouse", "lever", "ashby", "workable", "workday"):
            for slug in slugs:
                probes.append((ats, slug, _probe_one_ats(client, ats, slug)))

        # Run all probes in parallel and return the first positive result
        pending = asyncio.gather(*[p[2] for p in probes], return_exceptions=True)
        try:
            results = await asyncio.wait_for(pending, timeout=timeout * len(slugs))
        except asyncio.TimeoutError:
            results = []

        # Find the first non-None, non-exception result with jobs > 0
        best = None
        for r in results:
            if isinstance(r, tuple) and len(r) == 3:
                ats, jobs, meta = r
                if jobs is not None and jobs > 0:
                    best = {"ats": ats, "jobs": jobs, "name": name, **meta}
                    break

        if best is None:
            # Fall back to any 200 response even with 0 jobs (still a valid board)
            for r in results:
                if isinstance(r, tuple) and len(r) == 3:
                    ats, jobs, meta = r
                    if jobs is not None:
                        best = {"ats": ats, "jobs": jobs, "name": name, **meta}
                        break

    _DISCOVERY_CACHE[cache_key] = best
    return best


async def discover_companies_batch(
    names: List[str], timeout: float = 30.0
) -> Dict[str, Optional[Dict]]:
    """Discover ATS for a batch of company names in parallel."""
    tasks = {n: discover_company_ats(n, timeout=timeout) for n in names}
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    return {n: r for n, r in zip(tasks.keys(), results)}
