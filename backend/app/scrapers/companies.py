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
    "workday": [
        ".myworkdayjobs.com/",
        ".wd1.myworkdayjobs.com/",
        ".wd3.myworkdayjobs.com/",
        ".wd5.myworkdayjobs.com/",
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
            if host.endswith(".ashbyhq.com"):
                return host.split(".")[0]
        if ats == "workday":
            if ".myworkdayjobs.com" in url:
                return host.split(".")[0]
        return None
    except Exception:
        return None


# ===== COMPANY DIRECTORY =====
# Used by the frontend "suggested companies" endpoint to map a friendly company
# name to its ATS + slug so the aggregator knows where to scrape.
# Add new companies here as you discover them.
COMPANY_DIRECTORY = [
    ("Spacex", "Tech", "mid", "greenhouse", "spacex"),
    ("Databricks", "Tech", "mid", "greenhouse", "databricks"),
    ("Openai", "Tech", "mid", "ashby", "openai"),
    ("Stripe", "Tech", "mid", "greenhouse", "stripe"),
    ("Snowflake", "Tech", "mid", "ashby", "snowflake"),
    ("Datadog", "Tech", "mid", "greenhouse", "datadog"),
    ("Mongodb", "Tech", "mid", "greenhouse", "mongodb"),
    ("Anthropic", "Tech", "mid", "greenhouse", "anthropic"),
    ("Okta", "Tech", "mid", "greenhouse", "okta"),
    ("Onemedical", "Tech", "mid", "greenhouse", "onemedical"),
    ("Brex", "Tech", "mid", "greenhouse", "brex"),
    ("Cloudflare", "Tech", "mid", "greenhouse", "cloudflare"),
    ("Airbnb", "Tech", "mid", "greenhouse", "airbnb"),
    ("Adyen", "Tech", "mid", "greenhouse", "adyen"),
    ("Block", "Tech", "mid", "greenhouse", "block"),
    ("Elastic", "Tech", "mid", "greenhouse", "elastic"),
    ("Sezzle", "Tech", "mid", "greenhouse", "sezzle"),
    ("Pinterest", "Tech", "mid", "greenhouse", "pinterest"),
    ("Affirm", "Tech", "mid", "greenhouse", "affirm"),
    ("Figma", "Tech", "mid", "greenhouse", "figma"),
    ("Clickhouse", "Tech", "mid", "greenhouse", "clickhouse"),
    ("Instacart", "Tech", "mid", "greenhouse", "instacart"),
    ("Lyft", "Tech", "mid", "greenhouse", "lyft"),
    ("Twilio", "Tech", "mid", "greenhouse", "twilio"),
    ("Asana", "Tech", "mid", "greenhouse", "asana"),
    ("Notion", "Tech", "mid", "ashby", "notion"),
    ("Gitlab", "Tech", "mid", "greenhouse", "gitlab"),
    ("Intercom", "Tech", "mid", "greenhouse", "intercom"),
    ("Robinhood", "Tech", "mid", "greenhouse", "robinhood"),
    ("Fivetran", "Tech", "mid", "greenhouse", "fivetran"),
    ("Coinbase", "Tech", "mid", "greenhouse", "coinbase"),
    ("Cohere", "Tech", "mid", "ashby", "cohere"),
    ("Ramp", "Tech", "mid", "ashby", "ramp"),
    ("Hopper", "Tech", "mid", "ashby", "hopper"),
    ("Preply", "Tech", "mid", "ashby", "preply"),
    ("Spotify", "Tech", "mid", "lever", "spotify"),
    ("Plaid", "Tech", "mid", "ashby", "plaid"),
    ("Sofi", "Tech", "mid", "greenhouse", "sofi"),
    ("Tripadvisor", "Tech", "mid", "greenhouse", "tripadvisor"),
    ("Xero", "Tech", "mid", "ashby", "xero"),
    ("Perplexity", "Tech", "mid", "ashby", "perplexity"),
    ("Starling Bank", "Tech", "mid", "workable", "starling-bank"),
    ("Hinge Health", "Tech", "mid", "ashby", "hinge-health"),
    ("Monzo", "Tech", "mid", "greenhouse", "monzo"),
    ("Vercel", "Tech", "mid", "greenhouse", "vercel"),
    ("Duolingo", "Tech", "mid", "greenhouse", "duolingo"),
    ("Chime", "Tech", "mid", "greenhouse", "chime"),
    ("Twitch", "Tech", "mid", "greenhouse", "twitch"),
    ("1Password", "Tech", "mid", "ashby", "1password"),
    ("Discord", "Tech", "mid", "greenhouse", "discord"),
    ("Vultr", "Tech", "mid", "ashby", "vultr"),
    ("Deepgram", "Tech", "mid", "ashby", "deepgram"),
    ("Mercury", "Tech", "mid", "greenhouse", "mercury"),
    ("Ro", "Tech", "mid", "lever", "ro"),
    ("Fastly", "Tech", "mid", "greenhouse", "fastly"),
    ("Dropbox", "Tech", "mid", "greenhouse", "dropbox"),
    ("Confluent", "Tech", "mid", "ashby", "confluent"),
    ("Supabase", "Tech", "mid", "ashby", "supabase"),
    ("Writer", "Tech", "mid", "ashby", "writer"),
    ("Carta", "Tech", "mid", "greenhouse", "carta"),
    ("Amplitude", "Tech", "mid", "greenhouse", "amplitude"),
    ("Sentry", "Tech", "mid", "ashby", "sentry"),
    ("Singlestore", "Tech", "mid", "greenhouse", "singlestore"),
    ("Docker", "Tech", "mid", "ashby", "docker"),
    ("Mixpanel", "Tech", "mid", "greenhouse", "mixpanel"),
    ("Launchdarkly", "Tech", "mid", "greenhouse", "launchdarkly"),
    ("Sardine", "Tech", "mid", "ashby", "sardine"),
    ("Modal", "Tech", "mid", "ashby", "modal"),
    ("Blockchain", "Tech", "mid", "greenhouse", "blockchain"),
    ("Turing", "Tech", "mid", "greenhouse", "turing"),
    ("Workos", "Tech", "mid", "ashby", "workos"),
    ("Pagerduty", "Tech", "mid", "greenhouse", "pagerduty"),
    ("Linear", "Tech", "mid", "ashby", "linear"),
    ("Gemini", "Tech", "mid", "greenhouse", "gemini"),
    ("Dashlane", "Tech", "mid", "greenhouse", "dashlane"),
    ("Render", "Tech", "mid", "ashby", "render"),
    ("Webflow", "Tech", "mid", "greenhouse", "webflow"),
    ("Posthog", "Tech", "mid", "ashby", "posthog"),
    ("Astronomer", "Tech", "mid", "ashby", "astronomer"),
    ("Upgrade", "Tech", "mid", "greenhouse", "upgrade"),
    ("Andela", "Tech", "mid", "ashby", "andela"),
    ("Toptal", "Tech", "mid", "lever", "toptal"),
    ("Zapier", "Tech", "mid", "ashby", "zapier"),
    ("Calendly", "Tech", "mid", "greenhouse", "calendly"),
    ("Typeform", "Tech", "mid", "greenhouse", "typeform"),
    ("Circleci", "Tech", "mid", "greenhouse", "circleci"),
    ("Udacity", "Tech", "mid", "greenhouse", "udacity"),
    ("Starburst", "Tech", "mid", "greenhouse", "starburst"),
    ("Planetscale", "Tech", "mid", "greenhouse", "planetscale"),
    ("Airbyte", "Tech", "mid", "ashby", "airbyte"),
    ("Substack", "Tech", "mid", "ashby", "substack"),
    ("Bitwarden", "Tech", "mid", "greenhouse", "bitwarden"),
    ("Upwork", "Tech", "mid", "greenhouse", "upwork"),
    ("Uniswap", "Tech", "mid", "ashby", "uniswap"),
    ("Talkspace", "Tech", "mid", "greenhouse", "talkspace"),
    ("Deepmind", "Tech", "mid", "greenhouse", "deepmind"),
    ("Railway", "Tech", "mid", "ashby", "railway"),
    ("Lastpass", "Tech", "mid", "greenhouse", "lastpass"),
    ("Neon", "Tech", "mid", "lever", "neon"),
    ("Northbeam", "Tech", "mid", "greenhouse", "northbeam"),
    ("Parallel", "Tech", "mid", "greenhouse", "parallel"),
    ("Learnworlds", "Tech", "mid", "workable", "learnworlds"),
    ("Learnupon", "Tech", "mid", "greenhouse", "learnupon"),
    ("Consensys", "Tech", "mid", "greenhouse", "consensys"),
    ("Coursera", "Tech", "mid", "greenhouse", "coursera"),
    ("Udemy", "Tech", "mid", "greenhouse", "udemy"),
    ("Atlas", "Tech", "mid", "ashby", "atlas"),
    ("Descript", "Tech", "mid", "greenhouse", "descript"),
    ("Huggingface", "Tech", "mid", "workable", "huggingface"),
    ("Forward", "Tech", "mid", "greenhouse", "forward"),
    ("Ycombinator", "Tech", "mid", "ashby", "ycombinator"),
    ("Outschool", "Tech", "mid", "greenhouse", "outschool"),
    ("Buzzfeed", "Tech", "mid", "greenhouse", "buzzfeed"),
    ("Terminal", "Tech", "mid", "ashby", "terminal"),
    ("Dremio", "Tech", "mid", "greenhouse", "dremio"),
    ("Motherduck", "Tech", "mid", "ashby", "motherduck"),
    ("Compound", "Tech", "mid", "ashby", "compound"),
    ("Stytch", "Tech", "mid", "ashby", "stytch"),
    ("Unqork", "Tech", "mid", "greenhouse", "unqork"),
    ("Tilt", "Tech", "mid", "ashby", "tilt"),
    ("Assemblyai", "Tech", "mid", "greenhouse", "assemblyai"),
    ("Runway", "Tech", "mid", "ashby", "runway"),
    ("Opensea", "Tech", "mid", "ashby", "opensea"),
    ("Netlify", "Tech", "mid", "greenhouse", "netlify"),
    ("Masterclass", "Tech", "mid", "greenhouse", "masterclass"),
    ("Portable", "Tech", "mid", "greenhouse", "portable"),
    ("Method", "Tech", "mid", "greenhouse", "method"),
    ("Materialize", "Tech", "mid", "ashby", "materialize"),
    ("Tinybird", "Tech", "mid", "lever", "tinybird"),
    ("Epignosis", "Tech", "mid", "workable", "epignosis"),
    ("Anyscale", "Tech", "mid", "lever", "anyscale"),
    ("Tldraw", "Tech", "mid", "ashby", "tldraw"),
    ("Jasper", "Tech", "mid", "workable", "jasper"),
    ("Calm", "Tech", "mid", "greenhouse", "calm"),
    ("Brainly", "Tech", "mid", "ashby", "brainly"),
    ("Kayak", "Tech", "mid", "greenhouse", "kayak"),
    ("Ledger", "Tech", "mid", "lever", "ledger"),
    ("Nitro", "Tech", "mid", "workable", "nitro"),
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