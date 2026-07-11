"""Expand the curated COMPANY_DIRECTORY with verified ATS companies.

This script batches a large list of well-known company names against each ATS
API in parallel and writes the verified ones back to companies.py.

Usage:
    python scripts/expand_company_directory.py
"""

import asyncio
import json
import re
from typing import List, Tuple, Optional, Dict

import httpx


# Large list of well-known companies to probe. Covers tech, finance, healthcare,
# retail, media, education, and more. Many will fail — that's fine, we record
# only the verified ones.
WELL_KNOWN_COMPANIES: List[str] = [
    # Big tech
    "Airbnb", "Amazon", "Apple", "Google", "Meta", "Microsoft", "Netflix",
    "Stripe", "Square", "Block", "PayPal", "Spotify", "Twitter", "Uber",
    "Lyft", "Pinterest", "Snap", "Snapchat", "TikTok", "YouTube",
    "Twitch", "Reddit", "Discord", "Slack", "Zoom", "Dropbox", "Box",
    "Atlassian", "Adobe", "Salesforce", "Oracle", "SAP", "IBM", "Intel",
    "Nvidia", "AMD", "Cisco", "Dell", "HP", "Lenovo", "Asus", "Acer",
    # Fintech
    "Stripe", "Plaid", "Chime", "Robinhood", "Coinbase", "Kraken",
    "Gemini", "Binance", "Chainalysis", "Brex", "Ramp", "Mercury",
    "Wise", "Revolut", "Monzo", "Starling", "N26", "NuBank",
    "SoFi", "Affirm", "Klarna", "Adyen", "Checkout", "Marqeta",
    # SaaS / B2B
    "Notion", "Figma", "Miro", "Canva", "Asana", "Monday", "ClickUp",
    "Loom", "Calendly", "Typeform", "Webflow", "Framer", "Squarespace",
    "Wix", "Shopify", "BigCommerce", "Etsy", "eBay",
    "Datadog", "New Relic", "Splunk", "Sumo Logic", "Elastic",
    "MongoDB", "Cockroach Labs", "SingleStore", "Snowflake", "Databricks",
    "Confluent", "Redis Labs", "PlanetScale", "Supabase", "Neon",
    "Vercel", "Netlify", "Cloudflare", "Fastly", "Akamai",
    "GitHub", "GitLab", "Bitbucket", "CircleCI", "Travis CI",
    "Docker", "Kubernetes", "HashiCorp", "Pulumi", "Terraform",
    # AI / ML
    "OpenAI", "Anthropic", "Cohere", "Hugging Face", "Replicate",
    "Modal", "Anyscale", "Together AI", "Stability AI", "Runway",
    "Descript", "AssemblyAI", "Deepgram", "Perplexity", "You.com",
    "Sourcegraph", "Cursor", "Replit", "Codeium", "Windsurf",
    "Scale AI", "Labelbox", "Snorkel", "Weights & Biases",
    "Databricks", "DataRobot", "H2O.ai", "Hugging Face",
    # Healthcare / Bio
    "One Medical", "Forward", "Hinge Health", "Ginger", "Headspace",
    "Calm", "Talkspace", "Ro", "Hims", "Hers", "GoodRx", "Cake",
    "Carbon Health", "Babylon Health", "Spring Health", "Lyra Health",
    "Modern Health", "Wellframe", "Welltok", "Woebot", "Tempus",
    "Recursion", "Veeva", "Gilead", "Moderna", "BioNTech",
    "Pfizer", "Merck", "AbbVie", "Johnson & Johnson", "AstraZeneca",
    "Novartis", "Roche", "GlaxoSmithKline", "Sanofi", "Bayer",
    # Education
    "Coursera", "Udacity", "Udemy", "MasterClass", "Skillshare",
    "Khan Academy", "Duolingo", "Grammarly", "Preply", "Outschool",
    "Lambda School", "Guild Education", "Chegg", "Quizlet",
    "Brainly", "Khan Academy", "BYJU", "Unacademy",
    # Media / News
    "The New York Times", "The Washington Post", "BuzzFeed", "Vox Media",
    "The Verge", "TechCrunch", "Wired", "The Atlantic", "Forbes",
    "Bloomberg", "Reuters", "Associated Press", "Financial Times",
    "The Guardian", "BBC", "CNN", "Fox News", "HuffPost",
    "Substack", "Medium", "Patreon", "OnlyFans", "TikTok",
    # Retail / E-commerce
    "Walmart", "Target", "Costco", "Kroger", "Walgreens", "CVS",
    "Home Depot", "Lowe's", "Best Buy", "Macy's", "Nordstrom",
    "TJX", "Ross", "Dollar General", "Dollar Tree", "Big Lots",
    "Amazon", "eBay", "Etsy", "Shopify", "Wayfair", "Overstock",
    "Peloton", "Warby Parker", "Allbirds", "Glossier", "Casper",
    # Travel / Hospitality
    "Marriott", "Hilton", "Hyatt", "IHG", "Accor", "Airbnb",
    "Booking", "Expedia", "Kayak", "TripAdvisor", "Hopper",
    "Skyscanner", "Uber", "Lyft", "DoorDash", "Instacart",
    "Grubhub", "Deliveroo", "Just Eat", "Delivery Hero",
    "Starbucks", "McDonald's", "Shake Shack", "Sweetgreen",
    # Manufacturing / Industrial
    "Tesla", "Ford", "GM", "Boeing", "Airbus", "Lockheed Martin",
    "Raytheon", "Northrop Grumman", "General Dynamics", "BAE Systems",
    "Rolls-Royce", "Safran", "Thales", "GE", "Siemens", "3M",
    "Honeywell", "Emerson", "Caterpillar", "John Deere", "Komatsu",
    # Energy
    "ExxonMobil", "Chevron", "Shell", "BP", "ConocoPhillips",
    "TotalEnergies", "Eni", "Equinor", "Saudi Aramco",
    # Finance / Banking
    "Goldman Sachs", "Morgan Stanley", "JPMorgan Chase", "Bank of America",
    "Wells Fargo", "Citigroup", "BlackRock", "Fidelity", "Vanguard",
    "Charles Schwab", "E*Trade", "American Express", "Visa", "Mastercard",
    "HSBC", "Barclays", "Lloyds", "NatWest", "Santander", "UBS",
    "Credit Suisse", "Deutsche Bank", "Commerzbank", "UniCredit",
    "BNP Paribas", "Crédit Agricole", "Société Générale",
    "Royal Bank of Canada", "TD Bank", "Scotiabank", "BMO", "CIBC",
    # Insurance
    "Allstate", "Progressive", "Geico", "State Farm", "Liberty Mutual",
    "Travelers", "Prudential", "MetLife", "New York Life", "Aflac",
    "Nationwide", "Lincoln Financial", "Principal Financial",
    # Consulting / Accounting
    "McKinsey", "Boston Consulting Group", "Bain", "Deloitte",
    "PwC", "EY", "KPMG", "Accenture", "Capgemini", "Wipro",
    "Tata Consultancy Services", "Infosys", "Cognizant", "HCL",
    "Tech Mahindra", "Larsen & Toubro", "Reliance",
    # Logistics
    "FedEx", "UPS", "DHL", "Maersk", "CMA CGM", "COSCO",
    "XPO Logistics", "JB Hunt", "YRC Worldwide", "Old Dominion",
    # Telecom
    "AT&T", "Verizon", "T-Mobile", "Sprint", "Vodafone", "Orange",
    "Deutsche Telekom", "Telefonica", "BT", "Rogers", "Bell",
    "Telstra", "Optus", "Reliance Jio", "Airtel", "China Mobile",
    # Universities (often on Workday)
    "Harvard", "MIT", "Stanford", "Yale", "Princeton", "Columbia",
    "Cornell", "University of Pennsylvania", "Duke", "University of Chicago",
    "Northwestern", "NYU", "Georgetown", "Vanderbilt", "Rice",
    "Caltech", "Carnegie Mellon", "University of Michigan",
    "University of Wisconsin", "University of Illinois",
    "Purdue", "Iowa State", "Kansas State", "University of Missouri",
    "Oklahoma State", "Texas A&M", "University of Texas",
    "University of Arizona", "Arizona State", "University of Oregon",
    "University of Washington", "University of Colorado",
    "University of Utah", "BYU", "University of Nevada",
    "San Diego State", "UCSD", "UCI", "UCSB", "UCSC", "UCR", "UCSF",
    "UC Merced", "UC Berkeley", "UC Davis", "Scripps", "Cal Poly",
    "San Jose State", "San Francisco State", "CSU Bakersfield",
    "CSUN", "CSUF", "CSULB", "CSUDH", "CSUCI", "CSUSB", "CSUEB",
    "Sacramento State", "CSUSM", "CSUMB", "Humboldt", "Sonoma State",
    "Chico State", "Fresno State", "Stanislaus State",
    # Crypto / Web3
    "Coinbase", "Kraken", "Binance", "Gemini", "Bitstamp", "Bittrex",
    "Circle", "Ripple", "Chain", "Chainalysis", "Blockdaemon",
    "Figment", "Ledger", "OpenSea", "Uniswap", "Aave", "Compound",
    "Ethereum", "ConsenSys", "Chainlink", "MetaMask",
    # Other tech
    "Sentry", "PostHog", "Linear", "Height", "Dendron", "Obsidian",
    "Mixpanel", "Amplitude", "Heap", "LaunchDarkly", "PagerDuty",
    "Twilio", "SendGrid", "Mailchimp", "Segment", "Stripe",
    "Plaid", "Marqeta", "Bolt", "Brex", "Ramp", "Mercury",
    "Outreach", "Salesloft", "Gong", "Clari", "Zoominfo",
    "Snyk", "Aqua Security", "Wiz", "Lacework", "Orca Security",
    "Lookout", "Duo Security", "Okta", "Ping Identity",
    "JetBrains", "GitHub", "GitKraken", "Axosoft",
    "Harness", "Kong", "Spotify", "Netflix", "Disney",
    "Sony", "Samsung", "Toyota", "Honda", "Ford", "GM", "Tesla",
    "Nike", "Adidas", "Puma", "Lululemon", "Under Armour",
    "Patagonia", "North Face", "Columbia", "REI",
]


async def probe_greenhouse(client: httpx.AsyncClient, slug: str) -> Optional[int]:
    try:
        r = await client.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
        if r.status_code == 200:
            return len(r.json().get("jobs", []))
    except Exception:
        pass
    return None


async def probe_lever(client: httpx.AsyncClient, slug: str) -> Optional[int]:
    try:
        r = await client.get(f"https://api.lever.co/v0/postings/{slug}", params={"mode": "json"})
        if r.status_code == 200:
            d = r.json()
            return len(d) if isinstance(d, list) else len(d.get("postings", []))
    except Exception:
        pass
    return None


async def probe_ashby(client: httpx.AsyncClient, slug: str) -> Optional[int]:
    try:
        r = await client.get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
        if r.status_code == 200:
            d = r.json()
            if isinstance(d, list):
                return len(d)
            return len(d.get("postings", []))
    except Exception:
        pass
    return None


async def probe_workable(client: httpx.AsyncClient, slug: str) -> Optional[int]:
    try:
        r = await client.get(f"https://www.workable.com/api/accounts/{slug}?details=true")
        if r.status_code == 200:
            d = r.json()
            return len(d.get("jobs", []))
    except Exception:
        pass
    return None


async def probe_workday(client: httpx.AsyncClient, slug: str) -> Optional[Tuple[str, str, int]]:
    for wd in ("wd5", "wd3", "wd1"):
        for site in (slug, f"{slug}ExternalCareerSite", "External", "ExternalCareerSite"):
            try:
                r = await client.post(
                    f"https://{slug}.{wd}.myworkdayjobs.com/wday/cxs/{slug}/{site}/jobs",
                    json={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""},
                    headers={"Accept": "application/json", "Content-Type": "application/json"},
                )
                if r.status_code == 200:
                    total = int(r.json().get("total", 0))
                    if total > 0:
                        return (wd, site, total)
            except Exception:
                pass
    return None


def slugify(name: str) -> List[str]:
    s = name.lower().strip()
    for suffix in (", inc.", ", inc", " inc.", " inc", " corp.", " corp",
                   " corporation", " co.", " co", " ltd.", " ltd", " limited",
                   " llc", " gmbh", " sa", " ag", " pty"):
        if s.endswith(suffix):
            s = s[:-len(suffix)].strip()
    base = re.sub(r"[^a-z0-9]+", "", s)
    hyphen = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    out = []
    for v in (base, hyphen, s.replace(" ", "")):
        if v and v not in out:
            out.append(v)
    if " " in s:
        first = s.split()[0]
        if first not in out:
            out.append(first)
    # Special: "University of X" -> "ux", "ux.edu"
    if s.startswith("university of "):
        short = "u" + re.sub(r"[^a-z0-9]+", "", s[len("university of "):])[:3]
        if short not in out:
            out.append(short)
    return out


async def discover_one(client: httpx.AsyncClient, name: str) -> Optional[Dict]:
    slugs = slugify(name)
    if not slugs:
        return None
    for slug in slugs:
        # Try each ATS in parallel
        tasks = {
            "greenhouse": probe_greenhouse(client, slug),
            "lever": probe_lever(client, slug),
            "ashby": probe_ashby(client, slug),
            "workable": probe_workable(client, slug),
        }
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for (ats, _), r in zip(tasks.items(), results):
            if isinstance(r, int) and r > 0:
                return {"name": name, "ats": ats, "slug": slug, "jobs": r}
        # Workday separately (slower)
        wd_result = await probe_workday(client, slug)
        if wd_result:
            return {"name": name, "ats": "workday", "slug": slug, "wd": wd_result[0], "site": wd_result[1], "jobs": wd_result[2]}
    return None


async def main():
    # Deduplicate
    seen = set()
    companies = []
    for c in WELL_KNOWN_COMPANIES:
        k = c.lower().strip()
        if k not in seen:
            seen.add(k)
            companies.append(c)
    print(f"Probing {len(companies)} companies...")

    found = []
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        # Process in batches of 10 to be polite
        batch_size = 10
        for i in range(0, len(companies), batch_size):
            batch = companies[i:i+batch_size]
            results = await asyncio.gather(*[discover_one(client, n) for n in batch])
            for name, r in zip(batch, results):
                if r:
                    found.append(r)
                    print(f"  ✓ {r['name']}: {r['ats']}/{r['slug']} ({r.get('jobs', 0)} jobs)")

    print(f"\n=== Verified: {len(found)} ===")
    by_ats = {}
    for f in found:
        by_ats[f["ats"]] = by_ats.get(f["ats"], 0) + 1
    print("By ATS:", by_ats)

    with open("/tmp/discovered_companies.json", "w") as f:
        json.dump(found, f, indent=2)
    print("\nWrote /tmp/discovered_companies.json")


if __name__ == "__main__":
    asyncio.run(main())
