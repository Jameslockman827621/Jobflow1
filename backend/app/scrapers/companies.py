"""
Curated list of companies using each ATS provider.
Start with tech companies known to use these platforms.

Sources:
- BuiltWith.com
- Public job pages
- Community contributions
"""

# Companies using Greenhouse ATS
GREENHOUSE_COMPANIES = [
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
    # UK companies
    "monzo",
    "revolut",
    "starling-bank",
    "deliveroo",
    "just-eat",
]

# Companies using Lever ATS
LEVER_COMPANIES = [
    "airbnb",
    "asana",
    "brex",
    "canva",
    "coursera",
    "discord",
    "figma",
    "gusto",
    "hubspot",
    "intercom",
    "kickstarter",
    "linkedin",  # ironic
    "medium",
    "pinterest",
    "reddit",
    "square",
    "uber",
    # UK companies
    "wise",
    "checkout.com",
    "klarna",
]

# Companies using Workable
WORKABLE_COMPANIES = [
    # Add known Workable users
    # Workable is popular with SMBs and agencies
]

# Companies with custom career pages (direct scraping)
CUSTOM_CAREER_PAGES = {
    "google": "https://careers.google.com/api/jobs",
    "microsoft": "https://careers.microsoft.com/api/jobs",
    "amazon": "https://www.amazon.jobs/api/jobs",
    "meta": "https://www.metacareers.com/api/jobs",
    "apple": "https://jobs.apple.com/api/jobs",
    "netflix": "https://jobs.netflix.com/api/jobs",
}
