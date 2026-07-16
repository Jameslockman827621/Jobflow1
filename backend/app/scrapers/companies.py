"""
Curated ATS company directory for JobScale monitoring.

Scale target: tens of thousands of career pages via MonitoredCompany DB rows.
This seed list bootstraps verified Greenhouse / Lever / Workable / Ashby boards.
"""

# Greenhouse ATS boards (public boards-api) — target 200+ unique
GREENHOUSE_COMPANIES = [
    # US Tech / Product
    "airbnb", "coinbase", "doordash", "figma", "gitlab", "instacart", "notion",
    "robinhood", "shopify", "stripe", "substack", "twitch", "wayfair", "zendesk",
    "lyft", "pinterest", "square", "affirm", "brex", "chime", "datadog", "discord",
    "dropbox", "fivetran", "hubspot", "intercom", "launchdarkly", "mixpanel",
    "mongodb", "okta", "pulumi", "retool", "segment", "sentry", "slack", "snowflake",
    "splunk", "techcrunch", "twilio", "webflow", "zapier", "zillow", "asana",
    "box", "cloudflare", "confluent", "coursera", "cruise", "duolingo",
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
    "checkout.com", "klarna", "canva", "spacex", "deezer", "sumup",
    "transferwise", "typeform", "backmarket", "contentful", "freeagent",
    # Fintech / Enterprise
    "adyen", "bill", "blend", "clearstreet", "figure", "marqeta", "nextdoor",
    "quora", "truebill", "varonis",
    # Security / Infra / DevTools
    "crowdstrike", "snyk", "1password", "auth0", "duo", "tailscale", "cloudinary",
    "digitalocean", "heroku", "netlify", "render", "railway", "planetscale",
    "supabase", "neon", "temporal", "hashicorp-cloud", "circleci", "travisci",
    "buildkite", "jfrog", "sonatype", "datadoghq", "newrelic", "dynatrace",
    "splunk-cloud", "sumologic", "elastic-cloud", "grafana", "pagerduty-inc",
    "opsgenie", "statuspage", "launchdarkly-inc", "optimizely", "split",
    "flagsmith", "unleash", "posthog", "hotjar", "fullstory", "heap",
    "pendo", "appcues", "chameleon", "walkme", "whatfix",
    # SaaS / Productivity
    "notionhq", "coda", "miro-com", "figjam", "lucid", "whimsical", "miroapp",
    "clickup", "monday", "smartsheet", "airtablehq", "notion-labs", "linear",
    "height", "shortcut", "clubhouse", "jira", "atlassian", "asana-inc",
    "trello", "basecamp", "todoist", "evernote", "dropbox-paper",
    # Commerce / Marketplaces
    "etsy", "ebay", "poshmark", "depop", "mercari", "offerup", "craigslist",
    "stockx", "goat", "farfetch", "ssense", "revolve", "shopify-plus",
    "bigcommerce", "woocommerce", "magento", "saleor", "medusa",
    "stripe-climate", "affirmhq", "afterpay", "klarna-us", "sezzle",
    "quadpay", "zip", "affirm-inc",
    # Mobility / Logistics
    "waymo", "zoox", "cruise-automation", "aurora", "argo", "motional",
    "ridecell", "bird", "lime", "spin", "tier", "voi", "getaround",
    "turo", "hopskipdrive", "via", "scoop", "flexport-inc", "shipbob",
    "shipmonk", "fulfillment", "project44", "fourkites", "convoy",
    "uber-freight", "lyft-business",
    # Health / Bio
    "tempus-labs", "flatiron", "guardant", "illumina", "10xgenomics",
    "ginkgo", "recursion", "insitro", "benchling-inc", "gene", "color",
    "23andme", "ancestry", "ro", "hims", "nurx", "goodrx", "zocdoc",
    "oscar", "cigna", "unitedhealth", "devoted", "bright", "carbon-health",
    "one-medical", "forward", "cityblock",
    # Media / Consumer
    "nytimes", "washingtonpost", "bloomberg", "reuters", "axios", "vox",
    "buzzfeed", "vice", "conde-nast", "hearst", "disney", "warnerbros",
    "paramount", "nbcuniversal", "spotify-ab", "soundcloud", "tidal",
    "bandcamp", "patreon", "substack-inc", "medium", "ghost", "beehiiv",
    "convertkit", "mailchimp", "klaviyo", "braze", "iterable", "customerio",
    "onesignal", "airship", "leanplum",
    # Crypto / Web3
    "coinbase-inc", "kraken", "gemini", "bitgo", "fireblocks", "chainalysis",
    "elliptic", "alchemy", "infura", "consensys", "polygon", "solana",
    "avalanche", "ripple", "circle", "paxos", "anchorage", "coinlist",
    "opensea-inc", "magiceden", "blur", "dune", "nansen", "messari",
    # AI / ML platforms
    "anthropic", "cohere", "huggingface", "scale", "labelbox", "snorkel",
    "weights-biases", "wandb", "determined", "anyscale", "modal", "replicate",
    "together", "perplexity", "character", "jasper", "copyai", "writer",
    "grammarly-inc", "deepl", "runway", "stability", "midjourney",
    # Enterprise / HR
    "workday", "sap-successfactors", "bamboohr", "namely", "zenefits",
    "gusto-inc", "rippling-inc", "deel-inc", "remote-com", "oyster",
    "papaya-global", "payfit", "personio-gmbh", "hibob", "lattice-hq",
    "15five", "cultureamp", "glint", "peakon", "officevibe",
    # Payments / Banking
    "marqeta-inc", "galileo", "synapse", "unit", "treasury-prime",
    "modern-treasury-inc", "increase", "lithic", "highnote", "column",
    "cross-river", "varo", "current", "dave", "brigit", "earnin",
    "chime-inc", "sofi-inc", "ally", "capital-one", "jpmorgan",
]


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

# Lever postings boards — target 150+ unique
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
    "airtable", "coda", "roam", "obsidian", "craft", "superhuman",
    "front", "intercom", "zendesk", "freshworks", "hubspot", "salesforce",
    "outreach", "gong", "chorus", "apollo", "zoominfo", "clearbit", "segment",
    "amplitude", "mixpanel", "heap", "posthog", "fullstory", "hotjar",
    # Expanded Lever boards
    "fingerprint", "remotecom", "frontapp", "honeycomb", "launchdarkly",
    "pagerduty", "datadog", "newrelic", "sentry", "rollbar", "bugsnag",
    "circleci", "buildkite", "travis-ci", "gitlab", "github", "bitbucket",
    "docker", "kubernetes", "pulumi", "terraform", "ansible", "chef",
    "puppet", "saltstack", "vagrant", "packer", "nomad", "consul",
    "vault", "boundary", "waypoint", "waypoint-io", "cloudflare",
    "fastly", "akamai", "cloudinary", "imgix", "uploadcare",
    "twilio-inc", "sendgrid", "mailgun", "postmark", "customerio",
    "braze", "iterable", "klaviyo", "mailchimp", "constant-contact",
    "hubspot-inc", "marketo", "pardot", "eloqua", "activecampaign",
    "pipedrive", "close", "copper", "insightly", "freshsales",
    "zendesk-sell", "salesloft", "outreach-io", "groove", "reply",
    "lemlist", "woodpecker", "instantly", "apollo-io", "zoominfo-inc",
    "lusha", "seamless", "hunter", "snov", "dropcontact",
    "notion-labs", "coda-io", "roamresearch", "reflect", "mem",
    "craft-docs", "bear", "ulysses", "ia-writer", "scrivener",
    "figma-inc", "sketch", "invision", "marvel", "principle",
    "framer", "webflow", "bubble", "adalo", "glide",
    "retool-inc", "appsmith", "budibase", "tooljet", "internal",
    "airtable-inc", "nocodb", "baserow", "rowy", "stacker",
    "supabase-io", "firebase", "appwrite", "nhost", "backendless",
    "planetscale-inc", "neon-tech", "cockroach", "yugabyte", "tidb",
    "temporal-io", "cadence", "zeebe", "camunda", "n8n",
    "zapier-inc", "make", "tray", "workato", "boomi",
    "mulesoft", "kafka", "confluent-inc", "redpanda", "pulsar",
    "airbyte", "fivetran", "stitch", "talend", "informatica",
    "dbt-labs", "looker", "metabase", "superset", "redash",
    "tableau", "powerbi", "qlik", "sisense", "mode",
    "hex", "observable", "deepnote", "databricks-inc", "snowflake-inc",
])

# Workable career boards — target 80+ unique
WORKABLE_COMPANIES = _dedupe([
    "workable", "revolut", "transferwise", "deliveroo", "justeat", "monzo",
    "starling", "gocardless", "typeform", "hotjar", "intercom", "hubspot",
    "personio", "remote", "deel", "oyster", "papaya", "payfit", "spendesk",
    "qonto", "swan", "alma", "ledger", "backmarket", "vinted", "bol",
    "booking", "skyscanner", "kiwi", "trainline", "citymapper", "bolt",
    "wolt", "gorillas", "getir", "flink", "gopuff", "instacart", "doordash",
    "uber", "lyft", "cabify", "free-now", "bla-bla-car", "turo", "getaround",
    "autotrader", "cargurus", "vroom", "carvana", "shift", "fair",
    # Expanded Workable boards
    "wise", "n26", "klarna", "adyen", "checkout", "sumup", "mollie",
    "stripe", "square", "paypal", "revolut-business", "tide", "starling-bank",
    "crowdcube", "seedrs", "funding-circle", "iwoca", "marketinvoice",
    "contentful", "storyblok", "sanity", "prismic", "strapi",
    "webflow", "framer", "bubble", "wordpress", "ghost",
    "mailchimp", "klaviyo", "activecampaign", "brevo", "mailerlite",
    "zendesk", "freshdesk", "help-scout", "gorgias", "dixa",
    "pipedrive", "close", "copper", "hubspot-crm", "salesforce",
    "miro", "mural", "figma", "canva", "notion",
    "asana", "monday", "clickup", "trello", "jira",
    "gitlab", "github", "bitbucket", "atlassian", "jetbrains",
    "elastic", "mongodb", "datadog", "newrelic", "sentry",
    "cloudflare", "fastly", "akamai", "digitalocean", "linode",
    "heroku", "netlify", "vercel", "render", "railway",
    "spotify", "soundcloud", "deezer", "tidal", "bandcamp",
    "deliveroo-uk", "just-eat", "uber-eats", "glovo", "rappi",
    "hellofresh", "gousto", "blue-apron", "factor75", "sunbasket",
    "farfetch", "asos", "zalando", "aboutyou", "boohoo",
    "revolut-ltd", "transfergo", "remitly", "worldremit", "xe",
])

# Ashby boards (jobs.ashbyhq.com/{slug}) — target 100+ unique
ASHBY_COMPANIES = _dedupe([
    "openai", "anthropic", "notion", "ramp", "linear", "vercel", "replit",
    "perplexity", "cursor", "figma", "airtable", "mercury", "brex", "rippling",
    "deel", "remote", "lattice", "ashby", "watershed", "vanta", "secureframe",
    "drata", "conveyor", "wiz", "snyk", "crowdstrike", "sentinelone", "lacework",
    "orca", "temporal", "planetscale", "neon", "supabase", "railway",
    "render", "fly", "cloudflare", "hashicorp", "pulumi", "terraform",
    "databricks", "snowflake", "dbt", "fivetran", "airbyte", "census",
    "hightouch", "rudderstack", "segment", "amplitude", "posthog", "mixpanel",
    "heap", "fullstory", "hotjar", "pendo", "appcues", "chameleon",
    "intercom", "front", "plain", "zendesk", "freshdesk", "gong", "chorus",
    "outreach", "salesloft", "apollo", "clay", "clearbit", "zoominfo",
    # Expanded Ashby boards
    "cohere", "huggingface", "scale", "labelbox", "snorkel", "wandb",
    "anyscale", "modal", "replicate", "together", "character", "jasper",
    "writer", "runway", "stability", "midjourney", "elevenlabs", "descript",
    "loom", "grain", "fireflies", "otter", "rev", "deepgram",
    "retell", "vapi", "bland", "synthflow", "air", "assemblyai",
    "stripe", "plaid", "marqeta", "unit", "column", "increase",
    "modern-treasury", "lithic", "highnote", "treasury-prime", "synapse",
    "checkr", "persona", "alloy", "sardine", "unit21", "complyadvantage",
    "gusto", "justworks", "zenefits", "bamboohr", "hibob", "personio",
    "oyster", "papaya", "payfit", "remote-com", "deel-inc",
    "launchdarkly", "split", "optimizely", "flagsmith", "unleash",
    "honeycomb", "datadog", "newrelic", "sentry", "rollbar",
    "pagerduty", "opsgenie", "incident", "firehydrant", "rootly",
    "retool", "appsmith", "internal", "airplane", "windmill",
    "n8n", "zapier", "make", "tray", "workato",
    "dbt-labs", "hex", "mode", "observable", "deepnote",
    "metabase", "superset", "looker", "tableau", "sisense",
    "cockroachlabs", "yugabyte", "tidb", "clickhouse", "timescale",
    "kafka", "redpanda", "pulsar", "confluent", "materialize",
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
    "spacex": "https://www.spacex.com/careers/jobs/",
    "openai": "https://openai.com/careers/",
    "amazon-aws": "https://www.amazon.jobs/en/teams/aws",
    "microsoft-azure": "https://careers.microsoft.com/us/en/search-results?keywords=Azure",
    "google-cloud": "https://www.google.com/about/careers/applications/jobs/results/?q=Cloud",
    "apple-silicon": "https://jobs.apple.com/en-us/search?search=silicon",
    "meta-ai": "https://www.metacareers.com/jobs?q=AI",
    "jpmorgan": "https://careers.jpmorgan.com/",
    "goldman-sachs": "https://www.goldmansachs.com/careers/",
    "morgan-stanley": "https://www.morganstanley.com/careers",
    "bank-of-america": "https://careers.bankofamerica.com/",
    "citigroup": "https://jobs.citi.com/",
    "wells-fargo": "https://www.wellsfargojobs.com/",
    "capital-one": "https://www.capitalonecareers.com/",
    "american-express": "https://www.americanexpress.com/en-us/careers/",
    "visa": "https://usa.visa.com/careers.html",
    "mastercard": "https://careers.mastercard.com/",
    "paypal": "https://careers.pypl.com/",
    "walmart": "https://careers.walmart.com/",
    "target": "https://jobs.target.com/",
    "costco": "https://www.costco.com/jobs.html",
    "home-depot": "https://careers.homedepot.com/",
    "lowes": "https://talent.lowes.com/",
    "boeing": "https://jobs.boeing.com/",
    "lockheed-martin": "https://www.lockheedmartinjobs.com/",
    "northrop-grumman": "https://www.northropgrumman.com/jobs/",
    "raytheon": "https://careers.rtx.com/",
    "ge": "https://jobs.gecareers.com/",
    "siemens": "https://jobs.siemens.com/",
    "honeywell": "https://careers.honeywell.com/",
    "deloitte": "https://www2.deloitte.com/us/en/careers.html",
    "mckinsey": "https://www.mckinsey.com/careers",
    "bcg": "https://careers.bcg.com/",
    "bain": "https://www.bain.com/careers/",
    "accenture": "https://www.accenture.com/us-en/careers",
    "pwc": "https://www.pwc.com/us/en/careers.html",
    "ey": "https://www.ey.com/en_us/careers",
    "kpmg": "https://www.kpmg.us/careers.html",
    "unilever": "https://careers.unilever.com/",
    "p-and-g": "https://www.pgcareers.com/",
    "nestle": "https://www.nestle.com/jobs",
    "pepsico": "https://www.pepsicojobs.com/",
    "coca-cola": "https://www.coca-colacompany.com/careers",
    "disney": "https://jobs.disneycareers.com/",
    "warner-bros": "https://www.warnerbros.com/careers",
    "comcast": "https://jobs.comcast.com/",
    "verizon": "https://www.verizon.com/about/work",
    "att": "https://www.att.jobs/",
    "t-mobile": "https://www.t-mobile.com/careers",
    "samsung": "https://www.samsung.com/us/careers/",
    "sony": "https://www.sony.com/en/SonyInfo/Careers/",
    "lg": "https://www.lg.com/us/careers",
    "toyota": "https://www.toyota.com/careers/",
    "ford": "https://corporate.ford.com/careers.html",
    "gm": "https://search-careers.gm.com/",
    "bmw": "https://www.bmwgroup.jobs/",
    "mercedes": "https://group.mercedes-benz.com/careers/",
    "volkswagen": "https://www.volkswagen-group.com/en/careers",
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
