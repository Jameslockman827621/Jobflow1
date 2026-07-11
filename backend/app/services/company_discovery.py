"""
Company Discovery Service

Probes Greenhouse, Lever, Ashby, and Workable APIs with a large list of
company names to discover which ATS each company uses. Builds a large
COMPANY_DIRECTORY automatically instead of maintaining it manually.

Usage:
    python3 -c "
    from app.services.company_discovery import discover_companies
    results = discover_companies()
    print(f'Discovered {len(results)} companies with active ATS boards')
    "
"""

import asyncio
import httpx
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor


# A large list of tech companies to probe.
# Sources: YC company directory, Fortune 500 tech, well-known startups,
# companies known to use modern ATS systems.
COMPANY_NAMES_TO_PROBE = [
    # Big tech
    "google", "apple", "microsoft", "amazon", "meta", "netflix", "adobe",
    "salesforce", "oracle", "ibm", "intel", "cisco", "dell", "hp",
    # Unicorns / late stage
    "stripe", "airbnb", "uber", "lyft", "pinterest", "snap", "square",
    "block", "coinbase", "robinhood", "discord", "figma", "notion",
    "canva", "shopify", "twilio", "datadog", "snowflake", "mongodb",
    "elastic", "confluent", "pagerduty", "gitlab", "github", "atlassian",
    "asana", "monday", "zoom", "slack", "dropbox", "box", "okta",
    "zendesk", "hubspot", "intercom", "segment", "mixpanel", "amplitude",
    # YC companies (recent batches)
    "ycombinator", "vercel", "supabase", "planetscale", "render", "railway",
    "fly", "modal", "anyscale", "replicate", "cohere", "perplexity",
    "sourcegraph", "linear", "height", "retool", "cron", "dendron",
    "cal", "calcom", "tldraw", "dub", "posthog", "dubco", "unkey",
    "diffbot", "deepgram", "assemblyai", "descript", "runway",
    # AI/ML
    "openai", "anthropic", "huggingface", "scale", "stability",
    "weights-biases", "wandb", "together", "ai21", "ai21labs",
    "glean", "tome", "jasper", "copyai", "writer",
    # Fintech
    "plaid", "mercury", "ramp", "brex", "divvy", "carta", "eventbrite",
    "wise", "revolut", "monzo", "starling-bank", "klarna", "chime",
    "affirm", "sofi", "upgrade", "checkout", "adyen", "stripe",
    # Crypto
    "kraken", "gemini", "blockchain", "consensys", "chainlink",
    "opensea", "uniswap", "compound", "aave", "ethereum",
    "coinbase", "circle", "blockfi", "celo", "filecoin",
    # DevTools
    "docker", "hashicorp", "circleci", "fastly", "cloudflare",
    "digitalocean", "linode", "vultr", "heroku", "netlify",
    "webpack", "vite", "babel", "eslint", "prettier",
    "sentry", "launchdarkly", "fivetran", "dbt", "airbyte",
    # Health/Bio
    "onemedical", "forward", "hinge-health", "ginger", "headspace",
    "calm", "talkspace", "ouro", "ro", "him", "hims",
    # EdTech
    "duolingo", "coursera", "udacity", "khan-academy", "lambda-school",
    "guild-education", "outschool", "preply", "masterclass", "skillshare",
    "udemy", "quizlet", "brainly",
    # Media/Entertainment
    "substack", "techcrunch", "verge", "vox", "buzzfeed",
    "twitch", "youtube", "spotify", "soundcloud", "anchor",
    # E-commerce
    "wayfair", "instacart", "doordash", "grubhub", "uber-eats",
    "etsy", "ebay", "walmart", "target", "costco",
    # Travel
    "expedia", "booking", "kayak", "tripadvisor", "airbnb",
    "hopper", "virgin", "spacex", "tesla", "boeing",
    # Security
    "crowdstrike", "okta", "auth0", "onepassword", "1password",
    "lastpass", "dashlane", "bitwarden", "cloudflare",
    # Remote/global
    "toptal", "upwork", "fiverr", "andela", "turing",
    "gitstart", "terminal", "parallel-staff",
    # More startups
    "lumon", "databricks", "dremio", "starburst", "presto",
    "trino", "decodable", "materialize", "risingwave",
    "pinot", "druid", "clickhouse", "singlestore",
    "rockset", "tinybird", "duckdb", "motherduck",
    "neon", "turso", "xata", "tursodatabase",
    "clerk", "workos", "stytch", "magic-link",
    "portkey", "portable", "northbeam", "loophouse",
    "sardine", "scope", "method", "grain",
    "parallel", "ledger", "northpass", "sezzle",
    "oti", "epignosis", "talentlms", "learnworlds",
    "learnupon", "absorb", "continu", "skyprep",
    "time-doctor", "timedoctor", "getahero",
    # Additional tech companies
    "agilent", "brightvision", "lemon", "lemon-io", "unqork",
    "blue-origin", "linktree", "dremio", "astronomer",
    "atlas", "atlasgeo", "webflow", "zapier", "loom",
    "calendly", "typeform", "formstack", "nitro",
    "grammarly", "deepmind", "deepmind-google",
    "accelerator", "y-combinator", "startup-school",
    "brex", "riffle", "fly", "tidemark",
    "veem", "wave", "freshbooks", "xero", "intuit",
    "avantage", "tilt", "stake", "atlas", "vox",
]


async def probe_greenhouse(company: str) -> Optional[Dict]:
    """Check if a company has a Greenhouse job board."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                job_count = len(data.get("jobs", []))
                if job_count > 0:
                    return {"name": company, "ats": "greenhouse", "slug": company, "job_count": job_count}
    except Exception:
        pass
    return None


async def probe_lever(company: str) -> Optional[Dict]:
    """Check if a company has a Lever job board."""
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                jobs = data if isinstance(data, list) else data.get("postings", [])
                if len(jobs) > 0:
                    return {"name": company, "ats": "lever", "slug": company, "job_count": len(jobs)}
    except Exception:
        pass
    return None


async def probe_ashby(company: str) -> Optional[Dict]:
    """Check if a company has an Ashby job board."""
    # Ashby slugs are case-sensitive — try a few capitalizations
    for slug in [company, company.capitalize(), company.title()]:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params={"includeCompensation": "true"})
                if resp.status_code == 200:
                    data = resp.json()
                    jobs = data.get("jobs", [])
                    if len(jobs) > 0:
                        return {"name": company, "ats": "ashby", "slug": slug, "job_count": len(jobs)}
        except Exception:
            pass
    return None


async def probe_workable(company: str) -> Optional[Dict]:
    """Check if a company has a Workable job board."""
    url = f"https://www.workable.com/api/accounts/{company}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params={"details": "true"}, follow_redirects=True)
            if resp.status_code == 200:
                data = resp.json()
                jobs = data if isinstance(data, list) else data.get("jobs", [])
                if len(jobs) > 0:
                    return {"name": company, "ats": "workable", "slug": company, "job_count": len(jobs)}
    except Exception:
        pass
    return None


async def probe_company(company: str) -> Optional[Dict]:
    """Probe all ATS providers for a single company."""
    # Try each ATS in parallel
    results = await asyncio.gather(
        probe_greenhouse(company),
        probe_lever(company),
        probe_ashby(company),
        probe_workable(company),
        return_exceptions=True,
    )
    # Return the first match (prioritize by ATS reliability)
    for result in results:
        if isinstance(result, dict):
            return result
    return None


async def probe_all_companies(companies: List[str], batch_size: int = 20) -> List[Dict]:
    """Probe all companies in batches to avoid overwhelming the APIs."""
    discovered = []
    for i in range(0, len(companies), batch_size):
        batch = companies[i:i + batch_size]
        print(f"  Discovery: probing batch {i // batch_size + 1}/{(len(companies) + batch_size - 1) // batch_size} ({len(batch)} companies)")
        tasks = [probe_company(c) for c in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, dict):
                discovered.append(result)
                print(f"    ✓ {result['name']} — {result['ats']} ({result['job_count']} jobs)")
    return discovered


def discover_companies(company_names: List[str] = None) -> List[Dict]:
    """Main entry point — probe a list of company names and return discovered ATS boards.

    Args:
        company_names: list of company slug names to probe. If None, uses the built-in list.

    Returns:
        List of {name, ats, slug, job_count} for each company with an active ATS board.
    """
    names = company_names or COMPANY_NAMES_TO_PROBE
    # Deduplicate
    names = list(dict.fromkeys(names))
    print(f"  Discovery: probing {len(names)} companies across Greenhouse/Lever/Ashby/Workable...")

    loop = asyncio.new_event_loop()
    try:
        results = loop.run_until_complete(probe_all_companies(names))
    finally:
        loop.close()

    # Sort by job count (most jobs first)
    results.sort(key=lambda x: x.get("job_count", 0), reverse=True)
    print(f"  Discovery: found {len(results)} companies with active ATS boards")
    return results


def generate_directory_code(discovered: List[Dict]) -> str:
    """Generate Python code for COMPANY_DIRECTORY from discovered companies."""
    lines = ["COMPANY_DIRECTORY = ["]
    for d in discovered:
        # Capitalize the name for display
        display_name = d["name"].replace("-", " ").replace("_", " ").title()
        lines.append(f'    ("{display_name}", "Tech", "mid", "{d["ats"]}", "{d["slug"]}"),')
    lines.append("]")
    return "\n".join(lines)


if __name__ == "__main__":
    results = discover_companies()
    print(f"\nDiscovered {len(results)} companies:")
    for r in results[:20]:
        print(f"  {r['name']:20s} — {r['ats']:10s} ({r['job_count']} jobs)")
    print(f"\n... and {len(results) - 20} more")
