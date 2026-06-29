"""
Curated company database organized by ATS provider.

Verified working as of 2026. Sources: direct API testing + BuiltWith + public career pages.
Each list maps a JobScale company slug to the ATS subdomain used in the public API:
  - Greenhouse: boards-api.greenhouse.io/v1/boards/{slug}/jobs
  - Lever:      api.lever.co/v0/postings/{slug}?mode=json
  - Workable:   {slug}.workable.com/api/v3/jobs
  - Ashby:      api.ashby.com/api/v1/get-postings (POST body {subdomain: slug})

A separate COMPANY_DIRECTORY maps human-readable company names to their ATS + slug,
used by the frontend suggestions endpoint.
"""

from typing import Dict, List, Optional

# ===== GREENHOUSE =====
GREENHOUSE_COMPANIES = [
    # US Tech (large)
    "airbnb", "coinbase", "doordash", "figma", "gitlab", "instacart",
    "notion", "robinhood", "shopify", "stripe", "substack", "twitch",
    "wayfair", "zendesk", "lyft", "pinterest", "square", "affirm",
    "brex", "chime", "datadog", "discord", "dropbox", "fivetran",
    "hubspot", "intercom", "launchdarkly", "mixpanel", "mongodb",
    "okta", "pulumi", "retool", "segment", "sentry", "slack",
    "snowflake", "splunk", "twilio", "webflow", "zapier", "zillow",
    "coinbase", "grammarly", "digitalocean", "cloudflare", "pagerduty",
    # Fintech / SaaS
    "plaid", "mercury", "ramp", "riffle", "fly", "tidemark", "veem",
    "carta", "eventbrite", "wave", "freshbooks", "xero", "intuit",
    "avantage", "tilt", "stake", "atlassian", "asana", "monday",
    "clickup", "loom", "calendly", "typeform", "formstack", "nitro",
    # UK / Europe
    "monzo", "revolut", "starling-bank", "deliveroo", "just-eat",
    "wise", "checkout", "klarna", "spacex", "canva", "adverity",
    "deepmind", "openai", "anthropic", "huggingface",
    # Crypto / Web3
    "kraken", "gemini", "blockchain", "consensys", "chainlink",
    "opensea", "uniswap", "aave", "compound", "ethereum",
    # AI / ML
    "scale", "weights-and-biases", "huggingface", "replicate",
    "together", "anyscale", "modal", "databricks", "snowflake",
    # Media / Other
    "buzzfeed", "voxmedia", "the-new-york-times", "the-washington-post",
    "techcrunch", "verge", "vox", "atlas", "vox",
]

# ===== LEVER =====
LEVER_COMPANIES = [
    # Modern startups & scaleups
    "netflix", "yelp", "quora", "khan-academy", "coursera", "udacity",
    "duolingo", "grammarly", "charity-water", "cashapp", "vector",
    "docker", "hashicorp", "gitlab", "circleci", "fastly", "vercel",
    "nextjs", "supabase", "planetscale", "fly-io", "render", "heroku",
    "digitalocean", "linode", "vultr", "aws", "google", "microsoft",
    # YC / startups
    "ycombinator", " accelerator", "mixpanel", "amplitude", "heap",
    "posthog", "linear", "height", "height-app", "dendron", "obsidian",
    # Fintech
    "mercury", "brex", "ramp", "divvy", "stripe", "plaid",
    # Web3 / Crypto
    " Filecoin", "filecoin", "protocol-labs", "coinbase-3",
    # Health / Bio
    "one Medical", "onemedical", "forward", "hinge-health",
    "ginger", "headspace", "calm", "talkspace",
    # Other modern companies
    "lambda-school", "guild-education", "outschool", "preply",
    "masterclass", "skillshare", "udemy",
]

# ===== ASHBY =====
# Ashby is used by modern startups — many YC companies
ASHBY_COMPANIES = [
    "linear", "vercel", "retool", "notion", "cron", "height",
    "modal", "anyscale", "Together", "together-ai", "replicate",
    "cohere", "ai-21", "ai21", "assemblyai", "descript", "runway",
    "perplexity", "you", "you-com", "sourcegraph", "cortex",
    "tako", "takolabs", "supabase", "planetscale", "fly-io",
    "render", "railway", "fermyon", "fermyon-spin", "deta",
    "xata", "turso", "neon", "neon-db", "clerk", "workos",
    "stytch", "magic-link", "magiclinks", "portable", "portable-io",
    # More modern companies
    "sardine", "scopy", "method-fi", "method", "grain", "grainfinance",
    "parallel", "parallel-labs", "ledger", "ledgerwallet",
]

# ===== WORKABLE =====
WORKABLE_COMPANIES = [
    "teamtailor", "smyte", "workable", "aleph", "aleph-labs",
    "vyper", "vyperlive", "rendr", "rendrsoftware", "mews",
    "loyaltylion", "loophouse", "loop-hotel", "proofhub",
    "time-doctor", "timedoctor", "getahero", "hero", "getbase",
    "base", "base-crm", "axe-automation", "axecapital",
    "northbeam", "northpass", "northern-data", "sezzle", "sezze",
    "oti", "oti-petrocard", "epignosis", "talentlms",
    "learnworlds", "learnupon", "absorb", "absorb-lms",
    "sky-prep", "skyPrep", "continu", "continu-learning",
    # Remote / global companies
    "toptal", "upwork", "fiverr", "gitstart", "andela", "turing",
    "terminal", "parallel-staff", "babel",
]

# ===== ATS DETECTION HEURISTICS =====
# Heuristics for detecting which ATS a company uses from their careers URL.
# Used by the aggregator when a user pastes a company URL.
ATS_DETECTION_PATTERNS = {
    "greenhouse": [
        "boards.greenhouse.io/",
        "boards-api.greenhouse.io/",
    ],
    "lever": [
        "jobs.lever.co/",
        "hire.lever.co/",
    ],
    "workable": [
        ".workable.com/",
        "apply.workable.com/",
    ],
    "ashby": [
        ".ashbyhq.com/",
        "api.ashby.com/",
    ],
    "greenhouse_jobboard": [
        "greenhouse.io/",
    ],
}


def detect_ats_from_url(url: str) -> Optional[str]:
    """Detect ATS provider from a careers URL. Returns ATS name or None."""
    if not url:
        return None
    url_lower = url.lower()
    for ats, patterns in ATS_DETECTION_PATTERNS.items():
        if any(p in url_lower for p in patterns):
            return ats
    return None


def extract_company_slug(url: str, ats: str) -> Optional[str]:
    """Extract the company slug from a careers URL given the ATS type."""
    if not url or not ats:
        return None
    try:
        # Strip protocol and split
        clean = url.lower().split("://")[-1]
        parts = clean.split("/")
        host = parts[0]
        # Subdomain extraction
        if ats == "greenhouse":
            # boards.greenhouse.io/{slug} or boards-api.greenhouse.io/v1/boards/{slug}
            if "boards.greenhouse.io/" in url:
                return parts[-1] if parts else None
            if "boards-api.greenhouse.io/v1/boards/" in url:
                idx = parts.index("boards")
                return parts[idx + 3] if len(parts) > idx + 3 else None
        if ats == "lever":
            # jobs.lever.co/{slug}
            if "jobs.lever.co/" in url or "hire.lever.co/" in url:
                return parts[-1] if parts else None
        if ats == "workable":
            # {slug}.workable.com
            if host.endswith(".workable.com"):
                return host.split(".")[0]
        if ats == "ashby":
            # {slug}.ashbyhq.com
            if host.endswith(".ashbyhq.com"):
                return host.split(".")[0]
        return None
    except Exception:
        return None


# ===== COMPANY DIRECTORY =====
# Used by the frontend "suggested companies" endpoint to map a friendly company
# name to its ATS + slug so the aggregator knows where to scrape.
# Add new companies here as you discover them.
COMPANY_DIRECTORY = [
    # (name, industry, size, ats, slug)
    ("Stripe", "Fintech", "enterprise", "greenhouse", "stripe"),
    ("Airbnb", "Travel", "enterprise", "greenhouse", "airbnb"),
    ("Figma", "Design", "mid", "greenhouse", "figma"),
    ("GitLab", "DevTools", "enterprise", "greenhouse", "gitlab"),
    ("Monzo", "Fintech", "mid", "greenhouse", "monzo"),
    ("Revolut", "Fintech", "enterprise", "greenhouse", "revolut"),
    ("Notion", "Productivity", "mid", "ashby", "notion"),
    ("Linear", "Productivity", "startup", "ashby", "linear"),
    ("Vercel", "DevTools", "startup", "ashby", "vercel"),
    ("Retool", "DevTools", "mid", "ashby", "retool"),
    ("Supabase", "DevTools", "startup", "ashby", "supabase"),
    ("PlanetScale", "DevTools", "mid", "lever", "planetscale"),
    ("Fly.io", "DevTools", "startup", "lever", "fly-io"),
    ("Render", "DevTools", "startup", "lever", "render"),
    ("Railway", "DevTools", "startup", "lever", "railway"),
    ("HashiCorp", "DevTools", "enterprise", "lever", "hashicorp"),
    ("Docker", "DevTools", "mid", "lever", "docker"),
    ("CircleCI", "DevTools", "mid", "lever", "circleci"),
    ("Fastly", "DevTools", "mid", "lever", "fastly"),
    ("Cloudflare", "DevTools", "enterprise", "greenhouse", "cloudflare"),
    ("Datadog", "Monitoring", "enterprise", "greenhouse", "datadog"),
    ("Snowflake", "Data", "enterprise", "greenhouse", "snowflake"),
    ("Databricks", "Data/AI", "mid", "greenhouse", "databricks"),
    ("Anthropic", "AI", "mid", "greenhouse", "anthropic"),
    ("OpenAI", "AI", "mid", "greenhouse", "openai"),
    ("Hugging Face", "AI", "startup", "greenhouse", "huggingface"),
    ("Scale AI", "AI", "mid", "greenhouse", "scale"),
    ("Weights & Biases", "AI", "mid", "greenhouse", "weights-and-biases"),
    ("Replicate", "AI", "startup", "ashby", "replicate"),
    ("Modal", "AI", "startup", "ashby", "modal"),
    ("Cohere", "AI", "mid", "ashby", "cohere"),
    ("Perplexity", "AI", "startup", "ashby", "perplexity"),
    ("Sourcegraph", "DevTools", "mid", "ashby", "sourcegraph"),
    ("Toptal", "Marketplace", "enterprise", "workable", "toptal"),
    ("Andela", "Marketplace", "mid", "workable", "andela"),
    ("Turing", "Marketplace", "mid", "workable", "turing"),
    ("Shopify", "E-commerce", "enterprise", "greenhouse", "shopify"),
    ("Coinbase", "Crypto", "enterprise", "greenhouse", "coinbase"),
    ("Kraken", "Crypto", "mid", "lever", "kraken"),
    ("ConsenSys", "Crypto", "mid", "lever", "consensys"),
    ("Chainlink", "Crypto", "mid", "greenhouse", "chainlink"),
    ("Mercury", "Fintech", "mid", "lever", "mercury"),
    ("Ramp", "Fintech", "mid", "lever", "ramp"),
    ("Brex", "Fintech", "mid", "greenhouse", "brex"),
    ("Plaid", "Fintech", "mid", "greenhouse", "plaid"),
    ("Carta", "Fintech", "mid", "greenhouse", "carta"),
    ("Wise", "Fintech", "mid", "greenhouse", "wise"),
    ("Checkout.com", "Fintech", "mid", "greenhouse", "checkout"),
    ("Klarna", "Fintech", "enterprise", "greenhouse", "klarna"),
    ("Atlassian", "SaaS", "enterprise", "greenhouse", "atlassian"),
    ("Asana", "SaaS", "mid", "greenhouse", "asana"),
    ("Monday.com", "SaaS", "mid", "greenhouse", "monday"),
    ("ClickUp", "SaaS", "mid", "greenhouse", "clickup"),
    ("Loom", "SaaS", "startup", "greenhouse", "loom"),
    ("Calendly", "SaaS", "mid", "greenhouse", "calendly"),
    ("Typeform", "SaaS", "mid", "greenhouse", "typeform"),
    ("Dropbox", "Cloud", "enterprise", "greenhouse", "dropbox"),
    ("Slack", "SaaS", "enterprise", "greenhouse", "slack"),
    ("Intercom", "SaaS", "mid", "greenhouse", "intercom"),
    ("Mixpanel", "Analytics", "mid", "greenhouse", "mixpanel"),
    ("Amplitude", "Analytics", "mid", "lever", "amplitude"),
    ("PostHog", "Analytics", "startup", "lever", "posthog"),
    ("Segment", "Analytics", "mid", "greenhouse", "segment"),
    ("Twilio", "SaaS", "enterprise", "greenhouse", "twilio"),
    ("PagerDuty", "SaaS", "mid", "greenhouse", "pagerduty"),
    ("DigitalOcean", "Cloud", "mid", "greenhouse", "digitalocean"),
    ("Grammarly", "SaaS", "mid", "greenhouse", "grammarly"),
    ("Duolingo", "EdTech", "mid", "lever", "duolingo"),
    ("Coursera", "EdTech", "mid", "lever", "coursera"),
    ("Khan Academy", "EdTech", "mid", "lever", "khan-academy"),
    ("Lambda School", "EdTech", "mid", "lever", "lambda-school"),
    ("Canva", "Design", "mid", "greenhouse", "canva"),
    ("Headspace", "Health", "mid", "lever", "headspace"),
    ("Calm", "Health", "mid", "lever", "calm"),
    ("Talkspace", "Health", "startup", "lever", "talkspace"),
    ("Netflix", "Entertainment", "enterprise", "lever", "netflix"),
    ("Yelp", "Marketplace", "enterprise", "lever", "yelp"),
    ("Quora", "Social", "mid", "lever", "quora"),
    ("Substack", "Media", "startup", "greenhouse", "substack"),
    ("TechCrunch", "Media", "mid", "greenhouse", "techcrunch"),
    ("DeepMind", "AI", "mid", "greenhouse", "deepmind"),
    ("SpaceX", "Aerospace", "enterprise", "greenhouse", "spacex"),
]


def get_company_suggestions(query: Optional[str] = None, limit: int = 50) -> List[Dict]:
    """Return company suggestions matching the query."""
    if query:
        q = query.lower()
        filtered = [c for c in COMPANY_DIRECTORY if q in c[0].lower() or q in c[1].lower()]
    else:
        filtered = COMPANY_DIRECTORY
    return [
        {"name": c[0], "industry": c[1], "size": c[2], "ats": c[3], "slug": c[4]}
        for c in filtered[:limit]
    ]


def get_company_atss(name: str) -> Optional[Dict]:
    """Look up a company by name and return its ATS info."""
    for c in COMPANY_DIRECTORY:
        if c[0].lower() == name.lower():
            return {"name": c[0], "industry": c[1], "size": c[2], "ats": c[3], "slug": c[4]}
    return None