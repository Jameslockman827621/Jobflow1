"""
Discover and validate ATS career pages at scale.

Probes Greenhouse / Lever / Ashby / Workable public endpoints and imports
survivors into MonitoredCompany.
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
    "deliveroo", "instacart", "uber", "flexport", "shipbob",
    "coursera", "duolingo", "grammarly", "canva", "miro",
    "hubspot", "intercom", "zendesk", "freshworks", "salesforce",
    "spotify", "soundcloud", "reddit", "quora", "medium", "substack",
    "nyt", "washingtonpost", "bloomberg", "reuters", "techcrunch",
    "nvidia", "intel", "amd", "qualcomm", "broadcom", "arm",
    "palantir", "anduril", "scaleai", "cruise", "waymo", "zoox",
    "sofi", "upstart", "marqeta", "galileo",
    "vanta", "drata", "secureframe", "wiz", "snyk", "crowdstrike",
    "github", "atlassian", "jetbrains", "postman",
    "shopify", "slack", "pagerduty", "honeycomb", "newrelic",
    "cockroachlabs", "planetscale", "neon", "supabase", "temporal",
    "circleci", "buildkite", "jfrog", "sonatype", "grafana",
    "optimizely", "split", "posthog", "fullstory", "heap", "pendo",
    "clickup", "monday", "smartsheet", "linear", "height", "shortcut",
    "etsy", "ebay", "poshmark", "stockx", "farfetch", "bigcommerce",
    "bird", "lime", "turo", "getaround", "convoy", "project44",
    "tempus", "flatiron", "illumina", "ginkgo", "recursion", "color",
    "zocdoc", "goodrx", "hims", "oscar", "devoted",
    "axios", "vox", "patreon", "beehiiv", "klaviyo", "braze", "iterable",
    "kraken", "gemini", "bitgo", "fireblocks", "chainalysis", "alchemy",
    "opensea", "magiceden", "circle", "ripple", "consensys",
    "cohere", "huggingface", "anyscale", "modal", "replicate", "together",
    "perplexity", "runway", "stability", "jasper", "writer",
    "workday", "bamboohr", "deel", "remote", "personio", "hibob",
    "lithic", "unit", "column", "increase", "modern-treasury",
    "checkr", "carta", "navan", "faire", "flexport", "whatnot",
    "verkada", "nuro", "opendoor", "thumbtack", "nextdoor", "doximity",
    "calendly", "loom", "superhuman", "front", "typeform", "contentful",
    "backmarket", "sumup", "gocardless", "truelayer", "checkout.com",
    "spacex", "duolingo", "grammarly", "canva", "miro",
    "1password", "auth0", "tailscale", "digitalocean", "netlify", "render",
    "railway", "heroku", "cloudinary", "imgix", "fastly",
    "sendgrid", "mailgun", "postmark", "onesignal", "customerio",
    "pipedrive", "close", "salesloft", "outreach", "gong", "chorus",
    "apollo", "zoominfo", "clearbit", "clay", "lusha",
    "airbyte", "census", "hightouch", "rudderstack", "dbt-labs",
    "looker", "metabase", "hex", "mode", "observable",
    "redpanda", "materialize", "clickhouse", "timescale", "cockroach",
    "appsmith", "budibase", "n8n", "make", "workato",
    "snorkel", "labelbox", "wandb", "determined", "character",
    "elevenlabs", "descript", "deepgram", "assemblyai",
    "persona", "alloy", "sardine", "unit21", "complyadvantage",
    "incident", "firehydrant", "rootly", "opsgenie",
    "flagsmith", "unleash", "whatfix", "walkme", "appcues",
    "chameleon", "pendo", "fullstory", "hotjar",
]

EXTRA_LEVER_CANDIDATES = [
    "wealthfront", "netflix", "duolingo", "eventbrite", "yelp", "box",
    "coursera", "fingerprint", "anduril", "samsara", "replit", "linear",
    "mercury", "deel", "remotecom", "gong", "outreach", "amplitude",
    "mixpanel", "posthog", "hotjar", "intercom", "frontapp",
    "palantir", "twitch", "spotify", "shopify", "grammarly", "quora",
    "affirm", "nuro", "scaleai", "ramp", "notion", "figma", "anthropic",
    "perplexity", "vercel", "brex", "rippling", "gusto", "lattice",
    "remote", "angelist", "wellfound", "productboard", "miro", "canva",
    "atlassian", "elastic", "hashicorp", "databricks", "snowflake",
    "confluent", "mongodb", "okta", "twilio", "plaid", "stripe",
    "coinbase", "kraken", "gemini", "bitgo", "fireblocks", "chainalysis",
    "opensea", "magiceden", "dune", "alchemy", "infura", "consensys",
    "monzo", "revolut", "starling", "n26", "wise", "checkout", "klarna",
    "adyen", "gocardless", "truelayer", "marqeta", "lithic",
    "modern-treasury", "airtable", "coda", "superhuman", "front",
    "zendesk", "freshworks", "hubspot", "salesforce", "salesloft",
    "apollo", "zoominfo", "clearbit", "segment", "heap", "fullstory",
    "honeycomb", "launchdarkly", "pagerduty", "datadog", "newrelic",
    "sentry", "circleci", "buildkite", "gitlab", "github", "docker",
    "pulumi", "terraform", "cloudflare", "fastly", "cloudinary",
    "sendgrid", "mailgun", "braze", "iterable", "klaviyo", "mailchimp",
    "pipedrive", "close", "copper", "webflow", "framer", "bubble",
    "retool", "appsmith", "supabase", "planetscale", "neon",
    "temporal", "zapier", "make", "airbyte", "fivetran", "dbt-labs",
    "looker", "metabase", "hex", "mode", "observable", "deepnote",
    "redpanda", "n8n", "workato", "tray", "confluent-inc",
    "notion-labs", "figma-inc", "sketch", "invision", "loom",
    "grain", "otter", "descript", "elevenlabs", "cohere",
    "huggingface", "anyscale", "modal", "replicate", "together",
    "checkr", "persona", "alloy", "sardine", "unit21",
    "incident", "firehydrant", "rootly", "opsgenie",
    "flagsmith", "unleash", "split", "optimizely",
    "census", "hightouch", "rudderstack", "clickhouse",
    "timescale", "cockroach", "yugabyte", "materialize",
    "labelbox", "snorkel", "wandb", "character", "jasper",
    "writer", "runway", "stability", "midjourney",
]

EXTRA_ASHBY_CANDIDATES = [
    "ramp", "linear", "ashby", "notion", "vercel", "replit", "anthropic",
    "openai", "cursor", "mercury", "brex", "rippling", "deel", "remote",
    "lattice", "vanta", "watershed", "temporal", "planetscale", "neon",
    "supabase", "posthog", "amplitude", "mixpanel", "intercom", "front",
    "perplexity", "figma", "airtable", "secureframe", "drata", "conveyor",
    "wiz", "snyk", "crowdstrike", "sentinelone", "lacework", "orca",
    "railway", "render", "fly", "cloudflare", "hashicorp", "pulumi",
    "databricks", "snowflake", "dbt", "fivetran", "airbyte", "census",
    "hightouch", "rudderstack", "segment", "heap", "fullstory", "hotjar",
    "pendo", "appcues", "chameleon", "plain", "zendesk", "freshdesk",
    "gong", "chorus", "outreach", "salesloft", "apollo", "clay",
    "clearbit", "zoominfo", "cohere", "huggingface", "scale", "labelbox",
    "snorkel", "wandb", "anyscale", "modal", "replicate", "together",
    "character", "jasper", "writer", "runway", "stability", "midjourney",
    "elevenlabs", "descript", "loom", "grain", "fireflies", "otter",
    "deepgram", "assemblyai", "stripe", "plaid", "marqeta", "unit",
    "column", "increase", "modern-treasury", "lithic", "highnote",
    "checkr", "persona", "alloy", "sardine", "unit21", "complyadvantage",
    "gusto", "justworks", "zenefits", "bamboohr", "hibob", "personio",
    "oyster", "papaya", "payfit", "launchdarkly", "split", "optimizely",
    "flagsmith", "unleash", "honeycomb", "datadog", "newrelic", "sentry",
    "pagerduty", "opsgenie", "incident", "firehydrant", "rootly",
    "retool", "appsmith", "airplane", "windmill", "n8n", "zapier",
    "make", "tray", "workato", "hex", "mode", "observable", "deepnote",
    "metabase", "superset", "looker", "tableau", "sisense",
    "cockroachlabs", "yugabyte", "tidb", "clickhouse", "timescale",
    "redpanda", "pulsar", "confluent", "materialize", "dbt-labs",
]

EXTRA_WORKABLE_CANDIDATES = [
    "workable", "revolut", "transferwise", "deliveroo", "justeat", "monzo",
    "starling", "gocardless", "typeform", "hotjar", "intercom", "hubspot",
    "personio", "remote", "deel", "oyster", "papaya", "payfit", "spendesk",
    "qonto", "swan", "alma", "ledger", "backmarket", "vinted", "bol",
    "booking", "skyscanner", "kiwi", "trainline", "citymapper", "bolt",
    "wolt", "gorillas", "getir", "flink", "gopuff", "instacart", "doordash",
    "uber", "lyft", "cabify", "free-now", "bla-bla-car", "turo", "getaround",
    "autotrader", "cargurus", "vroom", "carvana", "shift", "fair",
    "wise", "n26", "klarna", "adyen", "checkout", "sumup", "mollie",
    "stripe", "square", "paypal", "tide", "crowdcube", "seedrs",
    "contentful", "storyblok", "sanity", "prismic", "strapi",
    "webflow", "framer", "bubble", "wordpress", "ghost",
    "mailchimp", "klaviyo", "activecampaign", "brevo", "mailerlite",
    "zendesk", "freshdesk", "help-scout", "gorgias", "dixa",
    "pipedrive", "close", "copper", "salesforce", "miro", "mural",
    "figma", "canva", "notion", "asana", "monday", "clickup", "trello",
    "gitlab", "github", "bitbucket", "atlassian", "jetbrains",
    "elastic", "mongodb", "datadog", "newrelic", "sentry",
    "cloudflare", "fastly", "akamai", "digitalocean", "linode",
    "heroku", "netlify", "vercel", "render", "railway",
    "spotify", "soundcloud", "deezer", "tidal", "bandcamp",
    "glovo", "rappi", "hellofresh", "gousto", "blue-apron",
    "farfetch", "asos", "zalando", "aboutyou", "boohoo",
    "remitly", "worldremit", "transfergo", "xe",
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


async def _probe_workable(client: httpx.AsyncClient, slug: str) -> Optional[Dict]:
    """Probe Workable widget API, then company subdomain jobs API."""
    urls = [
        f"https://apply.workable.com/api/v1/widget/accounts/{slug}",
        f"https://{slug}.workable.com/api/v2/jobs",
    ]
    for url in urls:
        try:
            r = await client.get(url, timeout=15.0)
            if r.status_code != 200:
                continue
            data = r.json() or {}
            if isinstance(data, list):
                jobs = data
            else:
                jobs = data.get("jobs") or data.get("results") or []
                # Widget account endpoint may return account meta without jobs
                if not jobs and data.get("name"):
                    jobs = []  # valid account — count unknown
                    return {
                        "name": data.get("name") or slug.replace("-", " ").title(),
                        "slug": slug,
                        "ats_type": "workable",
                        "career_url": f"https://apply.workable.com/{slug}/",
                        "priority": "cold",
                        "job_count": 0,
                    }
            if not isinstance(jobs, list):
                continue
            return {
                "name": slug.replace("-", " ").title(),
                "slug": slug,
                "ats_type": "workable",
                "career_url": f"https://apply.workable.com/{slug}/",
                "priority": "warm" if len(jobs) >= 10 else "cold",
                "job_count": len(jobs),
            }
        except Exception:
            continue
    return None


async def discover_companies(
    greenhouse: Optional[List[str]] = None,
    lever: Optional[List[str]] = None,
    ashby: Optional[List[str]] = None,
    workable: Optional[List[str]] = None,
    concurrency: int = 20,
) -> Dict:
    gh = list({*(greenhouse or []), *EXTRA_GREENHOUSE_CANDIDATES})
    lv = list({*(lever or []), *EXTRA_LEVER_CANDIDATES})
    ash = list({*(ashby or []), *EXTRA_ASHBY_CANDIDATES})
    wk = list({*(workable or []), *EXTRA_WORKABLE_CANDIDATES})

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
            + [run(_probe_workable, s) for s in wk]
        )
        await asyncio.gather(*tasks)

    by_ats: Dict[str, int] = {}
    jobs_total = 0
    for row in found:
        by_ats[row["ats_type"]] = by_ats.get(row["ats_type"], 0) + 1
        jobs_total += int(row.get("job_count") or 0)

    return {
        "probed": len(gh) + len(lv) + len(ash) + len(wk),
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
