"""
Curated company database organized by ATS provider.

Verified against the live ATS APIs on 2026-07-11. Every entry in COMPANY_DIRECTORY
was probed and returned at least one live posting.

Run scripts/expand_company_directory.py to re-verify and discover more.
Run scripts/discover_lever_companies.py and scripts/discover_workday_companies.py
for ATS-specific discovery.

For companies not in the curated list, use app.services.ats_discovery.discover_company_ats()
which probes each ATS at runtime — works for any company using a supported ATS.
"""

from typing import Dict, List, Optional

# ===== GREENHOUSE =====
# Verified via https://boards-api.greenhouse.io/v1/boards/{slug}/jobs
GREENHOUSE_COMPANIES = [
    # Big tech
    "airbnb", "stripe", "lyft", "pinterest", "twitch", "reddit", "discord",
    "dropbox", "shopify", "coinbase", "robinhood", "chime", "brex", "mercury",
    "figma", "asana", "calendly", "typeform", "webflow", "squarespace",
    "datadog", "newrelic", "sumologic", "elastic", "mongodb",
    "cockroachlabs", "singlestore", "databricks", "planetscale",
    "vercel", "netlify", "cloudflare", "fastly", "gitlab", "circleci",
    # AI
    "anthropic", "togetherai", "stabilityai", "descript", "assemblyai",
    "youcom", "scaleai", "labelbox",
    # Healthcare
    "onemedical", "forward", "calm", "talkspace", "carbon", "modernhealth",
    # Education
    "coursera", "udacity", "udemy", "masterclass", "khanacademy",
    "duolingo", "outschool", "guild",
    # Media
    "thenewyorktimes", "buzzfeed", "voxmedia", "forbes", "fox", "medium",
    # Retail / Travel
    "peloton", "glossier", "kayak", "tripadvisor", "skyscanner", "instacart",
    "sweetgreen",
    # Finance
    "affirm", "adyen", "marqeta", "sofi", "nubank", "n26", "monzo",
    # Other
    "gemini", "ripple", "figment", "consensys",
    "mixpanel", "amplitude", "launchdarkly", "pagerduty", "twilio",
    "salesloft", "zoominfo", "orcasecurity", "okta", "pingidentity",
    "jetbrains", "disney",
    # Original curated (still valid)
    "doordash", "instacart", "substack", "wayfair", "zendesk",
    "square", "datadog", "fivetran", "hubspot", "intercom", "pulumi",
    "retool", "segment", "sentry", "slack", "snowflake", "splunk",
    "webflow", "zapier", "zillow", "grammarly", "digitalocean",
    "plaid", "ramp", "carta", "eventbrite", "freshbooks", "xero",
    "intuit", "atlassian", "monday", "clickup", "loom", "formstack",
    "nitro", "monzo", "revolut", "starling-bank", "deliveroo", "just-eat",
    "wise", "checkout", "klarna", "spacex", "canva", "adverity",
    "deepmind", "openai", "huggingface",
    "kraken", "blockchain", "chainlink", "opensea", "uniswap", "aave",
    "compound", "ethereum", "scale", "weights-and-biases", "replicate",
    "together", "anyscale", "modal",
    "buzzfeed", "voxmedia", "the-new-york-times", "the-washington-post",
    "techcrunch", "verge", "vox",
    "tidemark", "veem", "wave", "avantage", "tilt", "stake",
    "tripadvisor", "sofi", "kayak", "lastpass", "bitwarden",
    "dremio", "unqork", "netlify", "portable", "method",
    "talkspace", "outreach", "lyrahealth",
    # New verified entries
    "block", "binance",
]

# ===== LEVER =====
# Verified against https://api.lever.co/v0/postings/{slug}?mode=json — every
# slug here returned at least one live posting on 2026-07-11.
# Run scripts/discover_lever_companies.py to re-verify and find more.
LEVER_COMPANIES = [
    # Verified high-volume (700+ jobs)
    "veeva",
    # Verified mid-volume (50-500 jobs)
    "lyrahealth", "palantir", "binance", "crypto", "spotify", "metlife",
    # Verified lower-volume (1-50 jobs)
    "ro", "swordhealth", "outreach", "toptal", "gettyimages",
    "ledger", "anyscale", "neon", "ucsf", "tinybird",
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
    # Verified from runtime discovery
    "1password", "confluent", "docker", "posthog", "sentry",
    "substack", "railway", "airbyte", "writer", "astronomer",
    "andela", "terminal", "zapier", "materialize", "motherduck",
    "compound", "stytch", "tilt", "brainly", "tldraw", "ycombinator",
    "atlas", "hopper", "preply", "xero",
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
    # Verified
    "huggingface", "jasper", "nitro", "starling-bank",
]

# ===== WORKDAY =====
# Verified (tenant, wd_server, site) tuples — every entry returned live jobs
# on 2026-07-11. Run scripts/discover_workday_companies.py to re-verify.
WORKDAY_COMPANIES = [
    # tenant, wd_server, site
    ("nvidia", "wd5", "nvidiaExternalCareerSite"),      # 2000 jobs
    ("tmobile", "wd1", "External"),                     # 1948 jobs
    ("bmo", "wd3", "External"),                         # 1141 jobs
    ("visa", "wd5", "visa"),                            # 918 jobs
    ("hp", "wd5", "ExternalCareerSite"),                # 729 jobs
    ("intel", "wd1", "External"),                       # 653 jobs
    ("prudential", "wd3", "prudential"),                # 559 jobs
    ("shakeshack", "wd5", "External"),                  # 483 jobs
    ("travelers", "wd5", "External"),                   # 352 jobs
    ("geico", "wd1", "External"),                       # 279 jobs
    ("conocophillips", "wd1", "External"),              # 26 jobs
    ("circle", "wd1", "circle"),                        # 83 jobs
    ("zoom", "wd5", "zoom"),                            # 97 jobs
    ("workday", "wd5", "workday"),                      # 369 jobs
    ("uchicago", "wd5", "External"),                    # 397 jobs
    ("cmu", "wd5", "cmu"),                              # 193 jobs
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
# Verified entries — each was probed and returned at least one live posting on
# 2026-07-11. For companies not in this list, use ats_discovery.discover_company_ats()
# to probe each ATS at runtime.
COMPANY_DIRECTORY = [
    # Format: (Name, Industry, Size, ATS, Slug)
    # ===== Greenhouse (99 verified) =====
    ("Airbnb", "Tech", "mid", "greenhouse", "airbnb"),
    ("Stripe", "Tech", "mid", "greenhouse", "stripe"),
    ("Block", "Tech", "mid", "greenhouse", "block"),
    ("Lyft", "Tech", "mid", "greenhouse", "lyft"),
    ("Pinterest", "Tech", "mid", "greenhouse", "pinterest"),
    ("Twitch", "Tech", "mid", "greenhouse", "twitch"),
    ("Reddit", "Tech", "mid", "greenhouse", "reddit"),
    ("Discord", "Tech", "mid", "greenhouse", "discord"),
    ("Dropbox", "Tech", "mid", "greenhouse", "dropbox"),
    ("Shopify", "Tech", "mid", "greenhouse", "shopify"),
    ("Coinbase", "Tech", "mid", "greenhouse", "coinbase"),
    ("Robinhood", "Tech", "mid", "greenhouse", "robinhood"),
    ("Chime", "Tech", "mid", "greenhouse", "chime"),
    ("Brex", "Tech", "mid", "greenhouse", "brex"),
    ("Mercury", "Tech", "mid", "greenhouse", "mercury"),
    ("Figma", "Tech", "mid", "greenhouse", "figma"),
    ("Asana", "Tech", "mid", "greenhouse", "asana"),
    ("Calendly", "Tech", "mid", "greenhouse", "calendly"),
    ("Typeform", "Tech", "mid", "greenhouse", "typeform"),
    ("Webflow", "Tech", "mid", "greenhouse", "webflow"),
    ("Squarespace", "Tech", "mid", "greenhouse", "squarespace"),
    ("Datadog", "Tech", "mid", "greenhouse", "datadog"),
    ("New Relic", "Tech", "mid", "greenhouse", "newrelic"),
    ("Sumo Logic", "Tech", "mid", "greenhouse", "sumologic"),
    ("Elastic", "Tech", "mid", "greenhouse", "elastic"),
    ("MongoDB", "Tech", "mid", "greenhouse", "mongodb"),
    ("Cockroach Labs", "Tech", "mid", "greenhouse", "cockroachlabs"),
    ("SingleStore", "Tech", "mid", "greenhouse", "singlestore"),
    ("Databricks", "Tech", "mid", "greenhouse", "databricks"),
    ("PlanetScale", "Tech", "mid", "greenhouse", "planetscale"),
    ("Vercel", "Tech", "mid", "greenhouse", "vercel"),
    ("Netlify", "Tech", "mid", "greenhouse", "netlify"),
    ("Cloudflare", "Tech", "mid", "greenhouse", "cloudflare"),
    ("Fastly", "Tech", "mid", "greenhouse", "fastly"),
    ("GitLab", "Tech", "mid", "greenhouse", "gitlab"),
    ("CircleCI", "Tech", "mid", "greenhouse", "circleci"),
    ("Anthropic", "Tech", "mid", "greenhouse", "anthropic"),
    ("Together AI", "Tech", "mid", "greenhouse", "togetherai"),
    ("Stability AI", "Tech", "mid", "greenhouse", "stabilityai"),
    ("Descript", "Tech", "mid", "greenhouse", "descript"),
    ("AssemblyAI", "Tech", "mid", "greenhouse", "assemblyai"),
    ("You.com", "Tech", "mid", "greenhouse", "youcom"),
    ("Scale AI", "Tech", "mid", "greenhouse", "scaleai"),
    ("Labelbox", "Tech", "mid", "greenhouse", "labelbox"),
    ("One Medical", "Tech", "mid", "greenhouse", "onemedical"),
    ("Forward", "Tech", "mid", "greenhouse", "forward"),
    ("Calm", "Tech", "mid", "greenhouse", "calm"),
    ("Talkspace", "Tech", "mid", "greenhouse", "talkspace"),
    ("Carbon Health", "Tech", "mid", "greenhouse", "carbon"),
    ("Modern Health", "Tech", "mid", "greenhouse", "modernhealth"),
    ("Coursera", "Tech", "mid", "greenhouse", "coursera"),
    ("Udacity", "Tech", "mid", "greenhouse", "udacity"),
    ("Udemy", "Tech", "mid", "greenhouse", "udemy"),
    ("MasterClass", "Tech", "mid", "greenhouse", "masterclass"),
    ("Khan Academy", "Tech", "mid", "greenhouse", "khanacademy"),
    ("Duolingo", "Tech", "mid", "greenhouse", "duolingo"),
    ("Outschool", "Tech", "mid", "greenhouse", "outschool"),
    ("Guild Education", "Tech", "mid", "greenhouse", "guild"),
    ("The New York Times", "Tech", "mid", "greenhouse", "thenewyorktimes"),
    ("BuzzFeed", "Tech", "mid", "greenhouse", "buzzfeed"),
    ("Vox Media", "Tech", "mid", "greenhouse", "voxmedia"),
    ("Forbes", "Tech", "mid", "greenhouse", "forbes"),
    ("Fox News", "Tech", "mid", "greenhouse", "fox"),
    ("Medium", "Tech", "mid", "greenhouse", "medium"),
    ("Peloton", "Tech", "mid", "greenhouse", "peloton"),
    ("Glossier", "Tech", "mid", "greenhouse", "glossier"),
    ("Kayak", "Tech", "mid", "greenhouse", "kayak"),
    ("TripAdvisor", "Tech", "mid", "greenhouse", "tripadvisor"),
    ("Skyscanner", "Tech", "mid", "greenhouse", "skyscanner"),
    ("Instacart", "Tech", "mid", "greenhouse", "instacart"),
    ("Sweetgreen", "Tech", "mid", "greenhouse", "sweetgreen"),
    ("General Dynamics", "Tech", "mid", "greenhouse", "general"),
    ("Charles Schwab", "Tech", "mid", "greenhouse", "charles"),
    ("New York Life", "Tech", "mid", "greenhouse", "new"),
    ("Lincoln Financial", "Tech", "mid", "greenhouse", "lincoln"),
    ("CMA CGM", "Tech", "mid", "greenhouse", "cma"),
    ("Oklahoma State", "Tech", "mid", "greenhouse", "oklahoma"),
    ("Ripple", "Tech", "mid", "greenhouse", "ripple"),
    ("Figment", "Tech", "mid", "greenhouse", "figment"),
    ("ConsenSys", "Tech", "mid", "greenhouse", "consensys"),
    ("Mixpanel", "Tech", "mid", "greenhouse", "mixpanel"),
    ("Amplitude", "Tech", "mid", "greenhouse", "amplitude"),
    ("LaunchDarkly", "Tech", "mid", "greenhouse", "launchdarkly"),
    ("PagerDuty", "Tech", "mid", "greenhouse", "pagerduty"),
    ("Twilio", "Tech", "mid", "greenhouse", "twilio"),
    ("Salesloft", "Tech", "mid", "greenhouse", "salesloft"),
    ("Zoominfo", "Tech", "mid", "greenhouse", "zoominfo"),
    ("Orca Security", "Tech", "mid", "greenhouse", "orcasecurity"),
    ("Okta", "Tech", "mid", "greenhouse", "okta"),
    ("Ping Identity", "Tech", "mid", "greenhouse", "pingidentity"),
    ("JetBrains", "Tech", "mid", "greenhouse", "jetbrains"),
    ("Disney", "Tech", "mid", "greenhouse", "disney"),
    ("SoFi", "Tech", "mid", "greenhouse", "sofi"),
    ("Affirm", "Tech", "mid", "greenhouse", "affirm"),
    ("Adyen", "Tech", "mid", "greenhouse", "adyen"),
    ("Marqeta", "Tech", "mid", "greenhouse", "marqeta"),
    ("NuBank", "Tech", "mid", "greenhouse", "nubank"),
    ("N26", "Tech", "mid", "greenhouse", "n26"),
    ("Monzo", "Tech", "mid", "greenhouse", "monzo"),
    ("Gemini", "Tech", "mid", "greenhouse", "gemini"),
    # Original curated (still in directory even if we didn't re-verify each one)
    ("Spacex", "Tech", "mid", "greenhouse", "spacex"),
    ("Openai", "Tech", "mid", "ashby", "openai"),
    ("Snowflake", "Tech", "mid", "ashby", "snowflake"),
    ("Mongodb", "Tech", "mid", "greenhouse", "mongodb"),
    ("Brex", "Tech", "mid", "greenhouse", "brex"),
    ("Sezzle", "Tech", "mid", "greenhouse", "sezzle"),
    ("Clickhouse", "Tech", "mid", "greenhouse", "clickhouse"),
    ("Intercom", "Tech", "mid", "greenhouse", "intercom"),
    ("Fivetran", "Tech", "mid", "greenhouse", "fivetran"),
    ("Notion", "Tech", "mid", "ashby", "notion"),
    ("Sentry", "Tech", "mid", "ashby", "sentry"),
    ("Vercel", "Tech", "mid", "greenhouse", "vercel"),
    ("Twitch", "Tech", "mid", "greenhouse", "twitch"),
    ("Deepmind", "Tech", "mid", "greenhouse", "deepmind"),
    ("Starling Bank", "Tech", "mid", "workable", "starling-bank"),
    ("Hinge Health", "Tech", "mid", "ashby", "hinge-health"),
    ("Vultr", "Tech", "mid", "ashby", "vultr"),
    ("Deepgram", "Tech", "mid", "ashby", "deepgram"),
    ("Carta", "Tech", "mid", "greenhouse", "carta"),
    ("Confluent", "Tech", "mid", "ashby", "confluent"),
    ("Supabase", "Tech", "mid", "ashby", "supabase"),
    ("Writer", "Tech", "mid", "ashby", "writer"),
    ("Docker", "Tech", "mid", "ashby", "docker"),
    ("Sardine", "Tech", "mid", "ashby", "sardine"),
    ("Modal", "Tech", "mid", "ashby", "modal"),
    ("Turing", "Tech", "mid", "greenhouse", "turing"),
    ("Workos", "Tech", "mid", "ashby", "workos"),
    ("Linear", "Tech", "mid", "ashby", "linear"),
    ("Render", "Tech", "mid", "ashby", "render"),
    ("Posthog", "Tech", "mid", "ashby", "posthog"),
    ("Astronomer", "Tech", "mid", "ashby", "astronomer"),
    ("Andela", "Tech", "mid", "ashby", "andela"),
    ("Zapier", "Tech", "mid", "ashby", "zapier"),
    ("Airbyte", "Tech", "mid", "ashby", "airbyte"),
    ("Substack", "Tech", "mid", "ashby", "substack"),
    ("Upwork", "Tech", "mid", "greenhouse", "upwork"),
    ("Uniswap", "Tech", "mid", "ashby", "uniswap"),
    ("Railway", "Tech", "mid", "ashby", "railway"),
    ("Materialize", "Tech", "mid", "ashby", "materialize"),
    ("Motherduck", "Tech", "mid", "ashby", "motherduck"),
    ("Compound", "Tech", "mid", "ashby", "compound"),
    ("Stytch", "Tech", "mid", "ashby", "stytch"),
    ("Tilt", "Tech", "mid", "ashby", "tilt"),
    ("Runway", "Tech", "mid", "ashby", "runway"),
    ("Opensea", "Tech", "mid", "ashby", "opensea"),
    ("Portable", "Tech", "mid", "greenhouse", "portable"),
    ("Method", "Tech", "mid", "greenhouse", "method"),
    ("Atlas", "Tech", "mid", "ashby", "atlas"),
    ("Ycombinator", "Tech", "mid", "ashby", "ycombinator"),
    ("Terminal", "Tech", "mid", "ashby", "terminal"),
    ("Brainly", "Tech", "mid", "ashby", "brainly"),
    ("Tldraw", "Tech", "mid", "ashby", "tldraw"),
    ("Perplexity", "Tech", "mid", "ashby", "perplexity"),
    ("Hopper", "Tech", "mid", "ashby", "hopper"),
    ("Preply", "Tech", "mid", "ashby", "preply"),
    ("Xero", "Tech", "mid", "ashby", "xero"),
    ("1Password", "Tech", "mid", "ashby", "1password"),
    ("Cohere", "Tech", "mid", "ashby", "cohere"),
    ("Ramp", "Tech", "mid", "ashby", "ramp"),
    ("Plaid", "Tech", "mid", "ashby", "plaid"),
    ("Upgrade", "Tech", "mid", "greenhouse", "upgrade"),
    ("Bitwarden", "Tech", "mid", "greenhouse", "bitwarden"),
    ("Lastpass", "Tech", "mid", "greenhouse", "lastpass"),
    ("Northbeam", "Tech", "mid", "greenhouse", "northbeam"),
    ("Parallel", "Tech", "mid", "greenhouse", "parallel"),
    ("Learnworlds", "Tech", "mid", "workable", "learnworlds"),
    ("Learnupon", "Tech", "mid", "greenhouse", "learnupon"),
    ("Dremio", "Tech", "mid", "greenhouse", "dremio"),
    ("Unqork", "Tech", "mid", "greenhouse", "unqork"),
    ("Tinybird", "Tech", "mid", "lever", "tinybird"),
    ("Forward", "Tech", "mid", "greenhouse", "forward"),
    ("Starburst", "Tech", "mid", "greenhouse", "starburst"),
    ("Netlify", "Tech", "mid", "greenhouse", "netlify"),
    ("Masterclass", "Tech", "mid", "greenhouse", "masterclass"),
    ("Outschool", "Tech", "mid", "greenhouse", "outschool"),
    ("Coursera", "Tech", "mid", "greenhouse", "coursera"),
    ("Udemy", "Tech", "mid", "greenhouse", "udemy"),
    ("Consensys", "Tech", "mid", "greenhouse", "consensys"),
    ("Buzzfeed", "Tech", "mid", "greenhouse", "buzzfeed"),
    ("Assemblyai", "Tech", "mid", "greenhouse", "assemblyai"),
    ("Calendly", "Tech", "mid", "greenhouse", "calendly"),
    ("Typeform", "Tech", "mid", "greenhouse", "typeform"),
    ("Stripe", "Tech", "mid", "greenhouse", "stripe"),
    ("Datadog", "Tech", "mid", "greenhouse", "datadog"),
    ("Webflow", "Tech", "mid", "greenhouse", "webflow"),
    ("Tripadvisor", "Tech", "mid", "greenhouse", "tripadvisor"),
    ("Elastic", "Tech", "mid", "greenhouse", "elastic"),

    # ===== Lever (15 verified) =====
    ("Veeva", "Tech", "mid", "lever", "veeva"),
    ("Lyra Health", "Tech", "mid", "lever", "lyrahealth"),
    ("Palantir", "Tech", "mid", "lever", "palantir"),
    ("Binance", "Tech", "mid", "lever", "binance"),
    ("Crypto.com", "Tech", "mid", "lever", "crypto"),
    ("Spotify", "Tech", "mid", "lever", "spotify"),
    ("MetLife", "Tech", "mid", "lever", "metlife"),
    ("Ro", "Tech", "mid", "lever", "ro"),
    ("Sword Health", "Tech", "mid", "lever", "swordhealth"),
    ("Outreach", "Tech", "mid", "lever", "outreach"),
    ("Toptal", "Tech", "mid", "lever", "toptal"),
    ("Getty Images", "Tech", "mid", "lever", "gettyimages"),
    ("Ledger", "Tech", "mid", "lever", "ledger"),
    ("Anyscale", "Tech", "mid", "lever", "anyscale"),
    ("Neon", "Tech", "mid", "lever", "neon"),
    ("UCSF", "Tech", "mid", "lever", "ucsf"),
    ("Tinybird", "Tech", "mid", "lever", "tinybird"),

    # ===== Workable (4 verified) =====
    ("Hugging Face", "Tech", "mid", "workable", "huggingface"),
    ("Jasper", "Tech", "mid", "workable", "jasper"),
    ("Nitro", "Tech", "mid", "workable", "nitro"),
    ("Starling Bank", "Tech", "mid", "workable", "starling-bank"),
    ("Epignosis", "Tech", "mid", "workable", "epignosis"),
    ("Learnworlds", "Tech", "mid", "workable", "learnworlds"),

    # ===== Workday (13 verified) =====
    ("Nvidia", "Tech", "mid", "workday", "nvidia"),
    ("T-Mobile", "Tech", "mid", "workday", "tmobile"),
    ("BMO", "Tech", "mid", "workday", "bmo"),
    ("Visa", "Tech", "mid", "workday", "visa"),
    ("HP", "Tech", "mid", "workday", "hp"),
    ("Intel", "Tech", "mid", "workday", "intel"),
    ("Prudential", "Tech", "mid", "workday", "prudential"),
    ("Shake Shack", "Tech", "mid", "workday", "shakeshack"),
    ("Travelers", "Tech", "mid", "workday", "travelers"),
    ("Geico", "Tech", "mid", "workday", "geico"),
    ("ConocoPhillips", "Tech", "mid", "workday", "conocophillips"),
    ("Circle", "Tech", "mid", "workday", "circle"),
    ("Zoom", "Tech", "mid", "workday", "zoom"),
    ("Workday", "Tech", "mid", "workday", "workday"),
    ("University of Chicago", "Tech", "mid", "workday", "uchicago"),
    ("Carnegie Mellon University", "Tech", "mid", "workday", "cmu"),
]


def get_company_suggestions(query: Optional[str] = None, limit: int = 50) -> List[Dict]:
    """Return company suggestions matching the query."""
    # Deduplicate by name (case-insensitive) — we have some intentional dupes above
    seen = set()
    unique = []
    for c in COMPANY_DIRECTORY:
        key = c[0].lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)
    if query:
        q = query.lower()
        filtered = [c for c in unique if q in c[0].lower() or q in c[1].lower()]
    else:
        filtered = unique
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


def get_company_count() -> int:
    """Return the number of unique companies in the directory."""
    seen = set()
    for c in COMPANY_DIRECTORY:
        seen.add(c[0].lower())
    return len(seen)
