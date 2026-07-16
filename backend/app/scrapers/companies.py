"""
Curated ATS company directory for JobScale monitoring.

Scale target: tens of thousands of career pages via MonitoredCompany DB rows.
This seed list bootstraps verified Greenhouse / Lever / Workable / Ashby boards.
"""

# Greenhouse ATS boards (public boards-api)
GREENHOUSE_COMPANIES = [
    # US Tech / Product
    "airbnb", "coinbase", "doordash", "figma", "gitlab", "instacart", "notion",
    "robinhood", "shopify", "stripe", "substack", "twitch", "wayfair", "zendesk",
    "lyft", "pinterest", "square", "affirm", "brex", "chime", "datadog", "discord",
    "dropbox", "fivetran", "hubspot", "intercom", "launchdarkly", "mixpanel",
    "mongodb", "okta", "pulumi", "retool", "segment", "sentry", "slack", "snowflake",
    "splunk", "techcrunch", "twilio", "webflow", "zapier", "zillow", "asana",
    "asana", "box", "cloudflare", "confluent", "coursera", "cruise", "duolingo",
    "elastic", "grammarly", "hashicorp", "nuro", "opendoor", "pagerduty", "plaid",
    "postman", "reddit", "scaleai", "squarespace", "toast", "uber", "vercel",
    "wealthfront", "airtable", "amplitude", "benchling", "bilt", "bolt", "calendly",
    "carta", "checkr", "clever", "cockroachlabs", "databricks", "dbt-labs",
    "doximity", "faire", "flexport", "gusto", "honeycomb", "lattice", "loom",
    "mercury", "miro", "modern-treasury", "n26", "natera", "navan", "openai",
    "opensea", "personio", "ramp", "rippling", "samsara", "snap", "sofi",
    "spotify", "superhuman", "tempus", "theathletic", "thumbtack", "toasttab",
    "upstart", "vanta", "verkada", "whatnot", "wiz",
    # UK / Europe
    "monzo", "revolut", "starling-bank", "deliveroo", "just-eat", "wise",
    "checkout.com", "klarna", "canva", "spacex", "deezer", "bolt", "sumup",
    "transferwise", "typeform", "backmarket", "contentful", "freeagent",
    # Fintech / Enterprise
    "adyen", "bill", "blend", "clearstreet", "figure", "marqeta", "nextdoor",
    "opensea", "quora", "robinhood", "stripe", "truebill", "varonis",
]

# Deduplicate while preserving order
def _dedupe(items):
    seen = set()
    out = []
    for x in items:
        x = (x or "").strip().lower().replace(" ", "")
        if not x or x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


GREENHOUSE_COMPANIES = _dedupe(GREENHOUSE_COMPANIES)

# Lever postings boards
LEVER_COMPANIES = _dedupe([
    "netflix", "palantir", "twitch", "spotify", "shopify", "fing", "grammarly",
    "eventbrite", "box", "yelp", "quora", "coursera", "duolingo", "wealthfront",
    "affirm", "nuro", "samsara", "fingerprints", "anduril", "scaleai", "ramp",
    "notion", "figma", "anthropic", "perplexity", "replit", "vercel", "linear",
    "mercury", "brex", "rippling", "gusto", "lattice", "deel", "remote",
    "angelist", "wellfound", "productboard", "miro", "canva", "atlassian",
    "elastic", "hashicorp", "databricks", "snowflake", "confluent", "mongodb",
    "okta", "twilio", "plaid", "stripe", "coinbase", "kraken", "gemini",
    "bitgo", "fireblocks", "chainalysis", "opensea", "magiceden", "dune",
    "alchemy", "infura", "consensys", "polygon", "solana", "avalanche",
    "monzo", "revolut", "starling", "n26", "wise", "checkout", "klarna",
    "adyen", "gocardless", "truelayer", "marqeta", "lithic", "modern-treasury",
    "airtable", "coda", "notion", "roam", "obsidian", "craft", "superhuman",
    "front", "intercom", "zendesk", "freshworks", "hubspot", "salesforce",
    "outreach", "gong", "chorus", "apollo", "zoominfo", "clearbit", "segment",
    "amplitude", "mixpanel", "heap", "posthog", "fullstory", "hotjar",
])

# Workable career boards
WORKABLE_COMPANIES = _dedupe([
    "workable", "revolut", "transferwise", "deliveroo", "justeat", "monzo",
    "starling", "gocardless", "typeform", "hotjar", "intercom", "hubspot",
    "personio", "remote", "deel", "oyster", "papaya", "payfit", "spendesk",
    "qonto", "swan", "alma", "ledger", "backmarket", "vinted", "bol",
    "booking", "skyscanner", "kiwi", "trainline", "citymapper", "bolt",
    "wolt", "gorillas", "getir", "flink", "gopuff", "instacart", "doordash",
    "uber", "lyft", "cabify", "free-now", "bla-bla-car", "turo", "getaround",
    "autotrader", "cargurus", "vroom", "carvana", "shift", "fair",
])

# Ashby boards (jobs.ashbyhq.com/{slug})
ASHBY_COMPANIES = _dedupe([
    "openai", "anthropic", "notion", "ramp", "linear", "vercel", "replit",
    "perplexity", "cursor", "figma", "airtable", "mercury", "brex", "rippling",
    "deel", "remote", "lattice", "ashby", "watershed", "vanta", "secureframe",
    "drata", "conveyor", "wiz", "snyk", "crowdstrike", "sentinelone", "lacework",
    "orca", "wiz", "temporal", "planetscale", "neon", "supabase", "railway",
    "render", "fly", "cloudflare", "hashicorp", "pulumi", "terraform",
    "databricks", "snowflake", "dbt", "fivetran", "airbyte", "census",
    "hightouch", "rudderstack", "segment", "amplitude", "posthog", "mixpanel",
    "heap", "fullstory", "hotjar", "pendo", "appcues", "chameleon",
    "intercom", "front", "plain", "zendesk", "freshdesk", "gong", "chorus",
    "outreach", "salesloft", "apollo", "clay", "clearbit", "zoominfo",
])

# Custom / enterprise career pages (Playwright-friendly targets)
CUSTOM_CAREER_PAGES = {
    "google": "https://careers.google.com/jobs/results/",
    "microsoft": "https://careers.microsoft.com/v2/global/en/search",
    "amazon": "https://www.amazon.jobs/en/search",
    "apple": "https://jobs.apple.com/en-us/search",
    "meta": "https://www.metacareers.com/jobs",
    "netflix": "https://jobs.netflix.com/search",
    "salesforce": "https://careers.salesforce.com/en/jobs/",
    "oracle": "https://careers.oracle.com/",
    "ibm": "https://www.ibm.com/careers/search",
    "intel": "https://jobs.intel.com/",
    "nvidia": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
    "adobe": "https://careers.adobe.com/us/en/search-results",
    "cisco": "https://jobs.cisco.com/",
    "sap": "https://jobs.sap.com/",
    "uber": "https://www.uber.com/careers/list/",
    "airbnb": "https://careers.airbnb.com/",
    "spotify": "https://www.lifeatspotify.com/jobs",
    "tesla": "https://www.tesla.com/careers/search/",
    "spaceX": "https://www.spacex.com/careers/jobs/",
    "openai": "https://openai.com/careers/",
}


def all_seed_companies():
    """Flatten seed lists into (name, slug, ats_type, priority, career_url) tuples."""
    rows = []
    hot_gh = {"stripe", "airbnb", "coinbase", "figma", "notion", "datadog", "openai", "shopify"}
    hot_ashby = {"openai", "anthropic", "ramp", "linear", "notion", "vercel"}
    for slug in GREENHOUSE_COMPANIES:
        rows.append({
            "name": slug.replace("-", " ").replace(".", " ").title(),
            "slug": slug,
            "ats_type": "greenhouse",
            "priority": "hot" if slug in hot_gh else ("warm" if slug in GREENHOUSE_COMPANIES[:40] else "cold"),
            "career_url": f"https://boards.greenhouse.io/{slug}",
        })
    for slug in LEVER_COMPANIES:
        rows.append({
            "name": slug.replace("-", " ").title(),
            "slug": slug,
            "ats_type": "lever",
            "priority": "warm" if slug in LEVER_COMPANIES[:30] else "cold",
            "career_url": f"https://jobs.lever.co/{slug}",
        })
    for slug in WORKABLE_COMPANIES:
        rows.append({
            "name": slug.replace("-", " ").title(),
            "slug": slug,
            "ats_type": "workable",
            "priority": "cold",
            "career_url": f"https://apply.workable.com/{slug}/",
        })
    for slug in ASHBY_COMPANIES:
        rows.append({
            "name": slug.replace("-", " ").title(),
            "slug": slug,
            "ats_type": "ashby",
            "priority": "hot" if slug in hot_ashby else "warm",
            "career_url": f"https://jobs.ashbyhq.com/{slug}",
        })
    for slug, url in CUSTOM_CAREER_PAGES.items():
        rows.append({
            "name": slug.replace("-", " ").title(),
            "slug": slug.lower(),
            "ats_type": "custom",
            "priority": "warm",
            "career_url": url,
        })
    return rows


# Approximate directory capacity claim for product metrics (seed + import pipeline)
DIRECTORY_CAPACITY_TARGET = 50_000
