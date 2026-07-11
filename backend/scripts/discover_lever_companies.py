"""Discover real Lever customer subdomains that have active job postings.

Tests candidate slugs against https://api.lever.co/v0/postings/{slug}?mode=json
and prints the ones that return at least one posting.

Usage:
    python scripts/discover_lever_companies.py
"""

import asyncio
import httpx
import json
from typing import List, Tuple


# Comprehensive list of likely Lever customer subdomains.
# Sources: technologychecker.io, public knowledge, common startup names.
CANDIDATE_SLUGS: List[str] = [
    # Big tech / public companies
    "shopify", "klarna", "palantir", "coinbase", "databricks", "affirm",
    "veeva", "atlassian", "plaid", "rackspace", "xero", "1password",
    "gettyimages", "remote", "techstars", "yelp", "quora",
    "doordash", "lyft", "pinterest", "twilio", "shopify",
    "duolingo", "grammarly", "khan-academy", "khanacademy",
    "coursera", "udacity", "masterclass", "skillshare", "udemy",
    # Startups / scaleups
    "mercury", "brex", "ramp", "notion", "notionhq",
    "linear", "linearapp", "posthog", "sentry", "sentry-inc",
    "gitlab", "gitlab-inc", "circleci", "docker", "docker-inc",
    "hashicorp", "fastly", "vercel", "vercel-inc",
    "supabase", "planetscale", "fly-io", "render", "railway",
    "modal", "modal-labs", "replit", "replicate", "runway", "runway-ml",
    "huggingface", "hugging-face", "sourcegraph", "deepmind",
    "openai", "anthropic", "cohere", "ai21", "assemblyai",
    "descript", "perplexity", "figma", "figma-inc", "lattice",
    "lattice-inc", "loom", "loom-inc", "asana", "asana-inc",
    "mixpanel", "amplitude", "heap", "heapanalytics",
    "datadog", "datadoghq", "cloudflare", "cloudflare-inc",
    "stripe", "stripe-inc", "front", "frontapp",
    "nylas", "nylas-inc", "webflow", "webflow-inc",
    "earnin", "earnin-inc", "twitch", "twitch-tv",
    # Health / Bio
    "onemedical", "one-medical", "forward", "hinge-health",
    "ginger", "headspace", "calm", "talkspace",
    # Fintech
    "divvy", "plaid", "plaid-com", "brex", "brextech",
    "mercury", "mercury-tech", "ramp", "ramp-financial",
    # Education
    "lambda-school", "guild-education", "outschool", "preply",
    # YC / VC firms
    "ycombinator", "techstars", "500startups",
    # Web3
    "filecoin", "protocol-labs", "protocol-labs-2",
    # Others — common SaaS / tech companies
    "segment", "segment-io", "mixin", "mixpanel-inc",
    "launchdarkly", "launchdarkly-inc", "twilio-inc",
    "mongodb", "mongodb-inc", "okta", "okta-inc",
    "pulumi", "pulumi-inc", "retool", "retool-inc",
    "slack", "slack-inc", "snowflake", "snowflake-com",
    "splunk", "splunk-inc", "twilio", "twilio-inc",
    "webflow", "webflow-inc", "zapier", "zapier-inc",
    "zillow", "zillow-inc", "wise", "wise-inc",
    "checkout", "checkout-com", "klarna", "klarna-inc",
    "spacex", "spacex-inc", "canva", "canva-inc",
    # Additional known Lever customers
    "celo", "celo-org", "graphite", "graphite-inc",
    "honeycomb", "honeycomb-io", "hudson", "hudson-river",
    "huggingface", "deel", "deel-inc", "remote-com",
    "remote-inc", "toptal", "toptal-inc",
    "andela", "andela-inc", "gitlab", "gitlab-com",
    "marqeta", "marqeta-inc", "blend", "blend-inc",
    "blend-labs", "chime", "chime-inc",
    "cashapp", "square", "squareup",
    "block", "block-inc", "affirm", "affirm-inc",
    "marqeta", "marqeta-inc", "wise", "wise-inc",
    "coinbase", "coinbase-inc", "crypto", "crypto-com",
    # Healthcare / Bio
    "ged", "recursion", "recursion-pharm",
    "verteport", "verge", "verge-genomics",
    # News / Media
    "nytimes", "nyt", "newrelic", "newrelic-inc",
    "scalar", "scalar-inc", "fastly", "fastly-inc",
    # Infrastructure
    "aws", "google", "microsoft", "apple", "meta",
    "facebook", "netflix", "spotify", "amazon",
    # Additional modern startups
    "cron", "cron-inc", "height", "height-app",
    "dendron", "obsidian", "obsidian-inc",
    "posthog", "posthog-inc", "tako", "takolabs",
    "modal", "modal-inc", "anyscale", "anyscale-inc",
    "together", "together-ai", "replicate", "replicate-inc",
    "you", "you-com", "cortex", "cortex-inc",
    "fermyon", "fermyon-spin", "deta", "deta-inc",
    # Marketing / Sales
    "outreach", "outreach-io", "salesloft", "salesloft-inc",
    "gong", "gong-io", "clari", "clari-inc",
    # Security
    "snyk", "snyk-io", "aqua", "aqua-security",
    "wiz", "wiz-inc", "lacework", "lacework-inc",
    "orca", "orca-security", "permiso", "permiso-inc",
    # Database / Data
    "redis", "redis-inc", "redis-labs", "redislabs",
    "confluent", "confluent-inc", "mongodb", "mongodb-inc",
    "cockroach", "cockroach-labs", "cockroachdb",
    "singlestore", "singlestore-inc",
    # Observability
    "lightstep", "lightstep-inc", "honeycomb", "honeycomb-io",
    "logdna", "logdna-inc", "loophq", "loop",
    # Dev tools
    "jetbrains", "jetbrains-inc", "github", "github-inc",
    "gitkraken", "gitkraken-inc", "axosoft", "axosoft-inc",
    # Payments / Fintech
    "checkout", "checkout-com", "stripe", "stripe-inc",
    "plaid", "plaid-com", "marqeta", "marqeta-inc",
    "bolt", "bolt-com", "bolt-inc", "brix", "brix-inc",
    "rutter", "rutter-inc", "modern-treasury", "moderntreasury",
    "modern-treasury-inc", "plaid", "plaid-inc",
    # Generative AI
    "anthropic", "anthropic-inc", "openai", "openai-inc",
    "huggingface", "huggingface-inc", "cohere", "cohere-inc",
    "ai21", "ai21-labs", "replicate", "replicate-inc",
    "stability", "stability-ai", "stabilityai",
    "forefront", "forefront-ai", "forefront-inc",
    "character", "character-ai", "characterai",
    "scale", "scale-ai", "scaleai", "scale-inc",
    # Other
    "harness", "harness-inc", "kong", "kong-inc",
    "ping", "ping-identity", "okta", "okta-inc",
    "duo", "duo-security", "duo-inc",
    "lookout", "lookout-inc", "lookout-security",
    "fireblocks", "fireblocks-inc",
    "triple", "triple-whale", "triplewhale",
    "yuga", "yuga-labs", "yugalabs",
    "polygon", "polygon-inc", "polygon-technology",
    "chainalysis", "chainalysis-inc",
    "skyfire", "skyfire-systems", "skyfire-inc",
    "truepill", "truepill-inc", "alto", "alto-pharmacy",
    "hims", "hims-inc", "hims-and-hers", "hers",
    "roman", "roman-health", "ro", "ro-inc",
    "caret", "caret-inc", "caret-ai",
    # Communications
    "ringcentral", "ringcentral-inc", "dialpad", "dialpad-inc",
    "intercom", "intercom-inc", "intercom-com",
    "front", "frontapp", "front-inc",
    # More startups
    "clubhouse", "clubhouse-inc", "clubhouse-media",
    "discord", "discord-inc", "discord-com",
    "reddit", "reddit-inc",
    "patreon", "patreon-inc",
    "substack", "substack-inc",
    "kitchens", "kitchens-inc",
    "mixer", "mixer-inc", "mixer-com",
    "onlyfans", "onlyfans-inc",
    "tumblr", "tumblr-inc",
    "medium", "medium-inc",
    "vox", "vox-media", "voxmedia",
    "buzzfeed", "buzzfeed-inc", "buzzfeedcom",
    "verge", "verge-inc", "theverge",
    "techcrunch", "techcrunch-inc",
    "hackernews", "hacker-news",
    "businessinsider", "business-insider",
    # Industry specific
    "looker", "looker-inc",
    "domo", "domo-inc",
    "tableau", "tableau-inc",
    "qlik", "qlik-inc",
    "microstrategy", "microstrategy-inc",
    "sisense", "sisense-inc",
    "thoughtspot", "thoughtspot-inc",
    # E-commerce
    "shopify", "shopify-inc", "shopify-com",
    "bigcommerce", "bigcommerce-inc",
    "wix", "wix-inc",
    "squarespace", "squarespace-inc",
    "etsy", "etsy-inc",
    "ebay", "ebay-inc",
    "amazon", "amazon-inc",
    "walmart", "walmart-inc",
    "target", "target-inc",
    "costco", "costco-inc",
    # Finance
    "robinhood", "robinhood-inc",
    "fidelity", "fidelity-inc",
    "vanguard", "vanguard-inc",
    "schwab", "schwab-inc",
    "etrade", "etrade-inc",
    "m1finance", "m1-finance",
    "public", "public-com",
    "stash", "stash-inc",
    "acorns", "acorns-inc",
    "chime", "chime-inc",
    "current", "current-inc",
    "varo", "varo-inc",
    "n26", "n26-inc",
    "monzo", "monzo-inc",
    "starling", "starling-bank",
    "revolut", "revolut-inc",
    "nubank", "nubank-inc",
    "wise", "wise-inc",
    "remittance", "remitly", "remitly-inc",
    # Crypto
    "coinbase", "coinbase-inc",
    "kraken", "kraken-inc",
    "binance", "binance-inc",
    "gemini", "gemini-inc",
    "bitstamp", "bitstamp-inc",
    "bittrex", "bittrex-inc",
    "circle", "circle-inc",
    "ripple", "ripple-inc",
    "chain", "chain-inc",
    "chainalysis", "chainalysis-inc",
    "blockdaemon", "blockdaemon-inc",
    "figment", "figment-inc",
    "chocolate", "chocolate-inc",
    "ledger", "ledger-inc",
    # Travel
    "airbnb", "airbnb-inc",
    "booking", "booking-com",
    "expedia", "expedia-inc",
    "kayak", "kayak-inc",
    "hopper", "hopper-inc",
    "skyscanner", "skyscanner-inc",
    "lufthansa", "lufthansa-inc",
    "uber", "uber-inc",
    "lyft", "lyft-inc",
    "grab", "grab-inc",
    "didi", "didi-inc",
    # Food
    "doordash", "doordash-inc",
    "ubereats", "uber-eats",
    "grubhub", "grubhub-inc",
    "instacart", "instacart-inc",
    "delivery", "delivery-hero",
    "just-eat", "justeat",
    "foodpanda", "foodpanda-inc",
    "wolt", "wolt-inc",
    # Real Estate
    "zillow", "zillow-inc",
    "redfin", "redfin-inc",
    "compass", "compass-inc",
    "opendoor", "opendoor-inc",
    "airbnb", "airbnb-inc",
    " Sonder", "sonder",
    "fair", "fair-inc",
]


async def check_slug(client: httpx.AsyncClient, slug: str) -> Tuple[str, int]:
    """Return (slug, job_count) if the slug has jobs, else (slug, 0)."""
    try:
        r = await client.get(
            f"https://api.lever.co/v0/postings/{slug}",
            params={"mode": "json"},
        )
        if r.status_code != 200:
            return (slug, -1)
        data = r.json()
        if isinstance(data, list):
            return (slug, len(data))
        if isinstance(data, dict):
            return (slug, len(data.get("postings", [])))
        return (slug, 0)
    except Exception:
        return (slug, -1)


async def main():
    # Deduplicate
    candidates = list(dict.fromkeys(s.strip() for s in CANDIDATE_SLUGS if s.strip()))
    print(f"Testing {len(candidates)} candidate slugs...")

    active: List[Tuple[str, int]] = []
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        # Batch in groups of 25 to be polite
        batch_size = 25
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i + batch_size]
            results = await asyncio.gather(*[check_slug(client, s) for s in batch])
            for slug, count in results:
                if count > 0:
                    active.append((slug, count))
                    print(f"  ✓ {slug}: {count} jobs")

    active.sort(key=lambda x: -x[1])
    print(f"\n=== Active Lever companies found: {len(active)} ===")
    for slug, count in active:
        print(f"  {slug}: {count}")

    # Write to a JSON file for easy inspection
    with open("/tmp/lever_active.json", "w") as f:
        json.dump([{"slug": s, "jobs": c} for s, c in active], f, indent=2)
    print(f"\nWrote /tmp/lever_active.json")


if __name__ == "__main__":
    asyncio.run(main())
