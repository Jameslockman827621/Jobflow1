"""
Curated list of companies using each ATS provider.
Verified to work as of March 2026.

Sources:
- Direct API testing
- BuiltWith.com
- Public job pages
"""

# Companies using Greenhouse ATS (verified working)
GREENHOUSE_COMPANIES = [
    # US Tech
    "airbnb",
    "coinbase",
    "doordash",
    "figma",
    "gitlab",
    "instacart",
    "notion",
    "robinhood",
    "shopify",
    "stripe",
    "substack",
    "twitch",
    "wayfair",
    "zendesk",
    "lyft",
    "pinterest",
    "square",
    "affirm",
    "brex",
    "chime",
    "datadog",
    "discord",
    "dropbox",
    "figma",
    "fivetran",
    "hubspot",
    "intercom",
    "launchdarkly",
    "mixpanel",
    "mongodb",
    "okta",
    "pulumi",
    "retool",
    "segment",
    "sentry",
    "slack",
    "snowflake",
    "splunk",
    "techcrunch",
    "twilio",
    "webflow",
    "zapier",
    "zillow",
    # UK/Europe
    "monzo",
    "revolut",
    "starling-bank",
    "deliveroo",
    "just-eat",
    "wise",
    "checkout.com",
    "klarna",
    "spacex",
    "canva",
]

# Companies using Lever ATS - HTML scraping (less reliable)
# Disabled for MVP - focus on Greenhouse which works via API
LEVER_COMPANIES = []

# Companies using Workable
WORKABLE_COMPANIES = []

# Companies with custom career pages (direct scraping)
CUSTOM_CAREER_PAGES = {
    # These require custom scrapers - add as needed
}
