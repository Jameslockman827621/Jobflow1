"""
Discover and validate ATS career pages at scale.

Probes Greenhouse / Lever / Ashby public endpoints and imports survivors
into MonitoredCompany.
"""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from app.models.company import MonitoredCompany
from app.scrapers.companies import all_seed_companies
from app.services.company_directory import bulk_import, seed_monitored_companies


# Extra candidate slugs to probe beyond curated seed (common tech/fintech brands)
EXTRA_GREENHOUSE_CANDIDATES = [
    "airbnb", "stripe", "coinbase", "doordash", "figma", "gitlab", "datadog",
    "cloudflare", "plaid", "openai", "anthropic", "discord", "dropbox", "lyft",
    "pinterest", "robinhood", "affirm", "brex", "chime", "ramp", "rippling",
    "gusto", "lattice", "notion", "airtable", "asana", "box", "twilio", "okta",
    "mongodb", "snowflake", "databricks", "hashicorp", "elastic", "confluent",
    "sentry", "segment", "amplitude", "mixpanel", "zapier", "webflow", "vercel",
    "retool", "pulumi", "launchdarkly", "fivetran", "dbtlabs", "benchling",
    "samsara", "toast", "square", "block", "cashapp", "afterpay", "klarna",
    "adyen", "checkout", "wise", "revolut", "monzo", "starling", "n26",
    "deliveroo", "instacart", "uber", "lyft", "flexport", "shipbob",
    "coursera", "duolingo", "grammarly", "canva", "miro", "figma",
    "hubspot", "intercom", "zendesk", "freshworks", "salesforce",
    "spotify", "soundcloud", "reddit", "quora", "medium", "substack",
    "nyt", "washingtonpost", "bloomberg", "reuters", "techcrunch",
    "nvidia", "intel", "amd", "qualcomm", "broadcom", "arm",
    "palantir", "anduril", "scaleai", "cruise", "waymo", "zoox",
    "robinhood", "sofi", "upstart", "affirm", "marqeta", "galileo",
    "vanta", "drata", "secureframe", "wiz", "snyk", "crowdstrike",
    "gitlab", "github", "atlassian", "jetbrains", "postman", "hashicorp",
]

EXTRA_LEVER_CANDIDATES = [
    "wealthfront", "netflix", "duolingo", "eventbrite", "yelp", "box",
    "coursera", "fingerprint", "anduril", "samsara", "replit", "linear",
    "mercury", "deel", "remotecom", "gong", "outreach", "amplitude",
    "mixpanel", "posthog", "hotjar", "intercom", "frontapp",
]

EXTRA_ASHBY_CANDIDATES = [
    "ramp", "linear", "ashby", "notion", "vercel", "replit", "anthropic",
    "openai", "cursor", "mercury", "brex", "rippling", "deel", "remote",
    "lattice", "vanta", "watershed", "temporal", "planetscale", "neon",
    "supabase", "posthog", "amplitude", "mixpanel", "intercom", "front",
]


async def _probe_greenhouse(client: httpx.AsyncClient, slug: str) -> Optional[Dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        r = await client.get(url, timeout=15.0)
        if r.status_code != 200:
            return None
        jobs = (r.json() or {}).get("jobs") or []
        return {
            "name": slug.replace("-", " ").title(),
            "slug": slug,
            "ats_type": "greenhouse",
            "career_url": f"https://boards.greenhouse.io/{slug}",
            "priority": "hot" if len(jobs) >= 100 else ("warm" if len(jobs) >= 20 else "cold"),
            "job_count": len(jobs),
        }
    except Exception:
        return None


async def _probe_lever(client: httpx.AsyncClient, slug: str) -> Optional[Dict]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        r = await client.get(url, timeout=15.0)
        if r.status_code != 200:
            return None
        jobs = r.json() or []
        if not isinstance(jobs, list):
            return None
        return {
            "name": slug.replace("-", " ").title(),
            "slug": slug,
            "ats_type": "lever",
            "career_url": f"https://jobs.lever.co/{slug}",
            "priority": "warm" if len(jobs) >= 10 else "cold",
            "job_count": len(jobs),
        }
    except Exception:
        return None


async def _probe_ashby(client: httpx.AsyncClient, slug: str) -> Optional[Dict]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    try:
        r = await client.get(url, timeout=15.0)
        if r.status_code != 200:
            return None
        data = r.json() or {}
        jobs = data.get("jobs") or data.get("jobPostings") or []
        return {
            "name": slug.replace("-", " ").title(),
            "slug": slug,
            "ats_type": "ashby",
            "career_url": f"https://jobs.ashbyhq.com/{slug}",
            "priority": "hot" if len(jobs) >= 50 else "warm",
            "job_count": len(jobs),
        }
    except Exception:
        return None


async def discover_companies(
    greenhouse: Optional[List[str]] = None,
    lever: Optional[List[str]] = None,
    ashby: Optional[List[str]] = None,
    concurrency: int = 20,
) -> Dict:
    gh = list({*(greenhouse or []), *EXTRA_GREENHOUSE_CANDIDATES})
    lv = list({*(lever or []), *EXTRA_LEVER_CANDIDATES})
    ash = list({*(ashby or []), *EXTRA_ASHBY_CANDIDATES})

    sem = asyncio.Semaphore(concurrency)
    found: List[Dict] = []

    async with httpx.AsyncClient(follow_redirects=True, headers={"User-Agent": "JobScaleDiscovery/1.0"}) as client:
        async def run(probe, slug):
            async with sem:
                row = await probe(client, slug)
                if row:
                    found.append(row)

        tasks = (
            [run(_probe_greenhouse, s) for s in gh]
            + [run(_probe_lever, s) for s in lv]
            + [run(_probe_ashby, s) for s in ash]
        )
        await asyncio.gather(*tasks)

    by_ats: Dict[str, int] = {}
    jobs_total = 0
    for row in found:
        by_ats[row["ats_type"]] = by_ats.get(row["ats_type"], 0) + 1
        jobs_total += int(row.get("job_count") or 0)

    return {
        "probed": len(gh) + len(lv) + len(ash),
        "found": len(found),
        "by_ats": by_ats,
        "estimated_jobs": jobs_total,
        "companies": found,
    }


def discover_and_import(db: Session) -> Dict:
    """Sync wrapper: seed curated list, discover live boards, import survivors."""
    seed = seed_monitored_companies(db)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            discovery = asyncio.run(discover_companies())
        else:
            discovery = loop.run_until_complete(discover_companies())
    except RuntimeError:
        discovery = asyncio.run(discover_companies())
    # strip job_count before import
    payload = [
        {k: v for k, v in c.items() if k != "job_count"}
        for c in discovery["companies"]
    ]
    imported = bulk_import(db, payload)
    # refresh job counts for known rows
    for c in discovery["companies"]:
        row = (
            db.query(MonitoredCompany)
            .filter(MonitoredCompany.ats_type == c["ats_type"], MonitoredCompany.slug == c["slug"])
            .first()
        )
        if row:
            row.last_job_count = c.get("job_count") or 0
            row.priority = c.get("priority") or row.priority
            row.is_active = True
    db.commit()
    total = db.query(MonitoredCompany).filter(MonitoredCompany.is_active.is_(True)).count()
    return {
        "seed": seed,
        "discovery": {
            "probed": discovery["probed"],
            "found": discovery["found"],
            "by_ats": discovery["by_ats"],
            "estimated_jobs": discovery["estimated_jobs"],
        },
        "imported": imported,
        "monitored_total": total,
        "seed_catalog_size": len(all_seed_companies()),
    }
