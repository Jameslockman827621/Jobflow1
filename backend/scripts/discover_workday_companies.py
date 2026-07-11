"""Discover real Workday company (tenant, wd_server, site) combinations.

For each known tenant, visits the root URL https://{tenant}.{wd}.myworkdayjobs.com/
and follows redirects to find the actual site name. Then verifies the CXS API
returns jobs.

Usage:
    python scripts/discover_workday_companies.py
"""

import asyncio
import httpx
import re
import json
from typing import List, Tuple, Optional


# Verified Workday tenants from jobhire.ai Fortune 500 research (2026-06)
# Format: (tenant, wd_server)
KNOWN_TENANTS: List[Tuple[str, str]] = [
    ("walmart", "wd5"),
    ("exxonmobil", "wd5"),
    ("nvidia", "wd5"),
    ("pg", "wd5"),  # Procter & Gamble
    ("lowes", "wd5"),
    ("sysco", "wd5"),
    ("globalhr", "wd5"),  # RTX
    ("boeing", "wd1"),
    ("cat", "wd5"),  # Caterpillar
    ("msd", "wd5"),  # Merck
    ("allstate", "wd5"),
    ("pfizer", "wd1"),
    ("nationwide", "wd1"),
    ("synnex", "wd5"),  # TD Synnex
    ("tjx", "wd1"),
    ("comcast", "wd5"),  # careers redirects
    ("pepsico", "wd5"),
    ("disney", "wd5"),
    ("prudential", "wd5"),
    ("conocophillips", "wd5"),
    ("dollartree", "wd5"),
    ("johnsoncontrols", "wd5"),
    ("3m", "wd5"),
    ("travelers", "wd5"),
    ("fanniemae", "wd5"),
    ("cardinalhealth", "wd5"),
    ("mckesson", "wd5"),
    ("generaldynamics", "wd5"),
    # Other large enterprises commonly on Workday
    ("adobe", "wd5"),
    ("salesforce", "wd5"),
    ("stripe", "wd1"),
    ("servicenow", "wd5"),
    ("workday", "wd5"),
    ("intuit", "wd5"),
    ("visa", "wd5"),
    ("mastercard", "wd5"),
    ("paypal", "wd5"),
    ("americanexpress", "wd5"),
    ("target", "wd5"),
    ("att", "wd5"),
    ("tmobile", "wd5"),
    ("hsbc", "wd5"),
    ("barclays", "wd5"),
    ("lloyds", "wd5"),
    ("santander", "wd5"),
    ("universitytexas", "wd5"),
    ("ucdavis", "wd5"),
    ("ucla", "wd5"),
    ("berkeley", "wd5"),
    ("stanford", "wd5"),
    ("mit", "wd5"),
    ("harvard", "wd5"),
    ("yale", "wd5"),
    ("princeton", "wd5"),
    ("columbia", "wd5"),
    ("cornell", "wd5"),
    ("upenn", "wd5"),
    ("duke", "wd5"),
    ("uchicago", "wd5"),
    ("northwestern", "wd5"),
    ("nyu", "wd5"),
    ("georgetown", "wd5"),
    ("vanderbilt", "wd5"),
    ("rice", "wd5"),
    ("caltech", "wd5"),
    ("cmu", "wd5"),
    ("umich", "wd5"),
    ("wisc", "wd5"),
    ("illinois", "wd5"),
    ("purdue", "wd5"),
    ("iastate", "wd5"),
    ("k-state", "wd5"),
    ("missouri", "wd5"),
    ("okstate", "wd5"),
    ("tamu", "wd5"),
    ("utexas", "wd5"),
    ("arizona", "wd5"),
    ("asu", "wd5"),
    ("uoregon", "wd5"),
    ("washington", "wd5"),
    ("colorado", "wd5"),
    ("utah", "wd5"),
    ("byu", "wd5"),
    ("nevada", "wd5"),
    ("sdsu", "wd5"),
    ("ucsd", "wd5"),
    ("uci", "wd5"),
    ("ucsb", "wd5"),
    ("ucsc", "wd5"),
    ("ucr", "wd5"),
    ("ucsf", "wd5"),
    ("ucmerced", "wd5"),
    ("berkeley", "wd5"),
    ("ucdavis", "wd5"),
    ("scripps", "wd5"),
    ("calpoly", "wd5"),
    ("cpp", "wd5"),
    ("cpp", "wd5"),
    ("sjsu", "wd5"),
    ("sfsu", "wd5"),
    ("csub", "wd5"),
    ("csun", "wd5"),
    ("csuf", "wd5"),
    ("csulb", "wd5"),
    ("csudh", "wd5"),
    ("csuci", "wd5"),
    ("csusb", "wd5"),
    ("csueb", "wd5"),
    ("csus", "wd5"),
    ("csusm", "wd5"),
    ("csumb", "wd5"),
    ("csumb", "wd5"),
    ("humboldt", "wd5"),
    ("sonoma", "wd5"),
    ("chico", "wd5"),
    ("fresno", "wd5"),
    ("bakersfield", "wd5"),
    ("stanislaus", "wd5"),
    ("montereybay", "wd5"),
    ("maritime", "wd5"),
    ("mendocino", "wd5"),
    ("sacramento", "wd5"),
]

SITE_REDIRECT_RE = re.compile(
    r"https?://[\w.-]+\.wd\d+\.myworkdayjobs\.com/(?:en-US/)?([\w-]+)",
    re.IGNORECASE,
)


async def discover_site(client: httpx.AsyncClient, tenant: str, wd: str) -> Optional[str]:
    """Visit the root URL and follow redirects to find the actual site name."""
    url = f"https://{tenant}.{wd}.myworkdayjobs.com/"
    try:
        # Don't follow redirects automatically — we want to inspect them
        r = await client.get(url, follow_redirects=False)
        # 301/302/303/307/308 — look in Location header
        if r.status_code in (301, 302, 303, 307, 308):
            location = r.headers.get("location", "")
            m = SITE_REDIRECT_RE.search(location)
            if m:
                return m.group(1)
        # If we got a 200, try to scrape the HTML for a jobs URL
        if r.status_code == 200:
            text = r.text
            # Look for embedded site reference
            for m in SITE_REDIRECT_RE.finditer(text):
                return m.group(1)
        # Some tenants redirect to a path like /en-US/{site}
        if r.status_code in (301, 302, 303, 307, 308):
            location = r.headers.get("location", "")
            # Try absolute URL parsing
            if location.startswith("/"):
                # Strip /en-US/ prefix
                m = re.match(r"/(?:en-US/)?([\w-]+)", location)
                if m:
                    return m.group(1)
    except Exception:
        return None
    return None


async def verify_site(client: httpx.AsyncClient, tenant: str, wd: str, site: str) -> Tuple[bool, int, int]:
    """Verify a (tenant, wd, site) returns jobs via the CXS API."""
    url = f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    try:
        r = await client.post(
            url,
            json={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        if r.status_code == 200:
            data = r.json()
            return (True, len(data.get("jobPostings", [])), int(data.get("total", 0)))
    except Exception:
        pass
    return (False, 0, 0)


async def main():
    found = []
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        for tenant, wd in KNOWN_TENANTS:
            site = await discover_site(client, tenant, wd)
            if not site:
                # Try common fallback site names
                for candidate in (
                    f"{tenant}ExternalCareerSite",
                    f"{tenant.capitalize()}ExternalCareerSite",
                    "ExternalCareerSite",
                    "External",
                    "careers",
                    tenant,
                ):
                    ok, n, total = await verify_site(client, tenant, wd, candidate)
                    if ok and n > 0:
                        site = candidate
                        found.append((tenant, wd, site, n, total))
                        print(f"  ✓ {tenant}.{wd} [{site}]: {n} jobs (total: {total})")
                        break
                continue
            ok, n, total = await verify_site(client, tenant, wd, site)
            if ok and n > 0:
                found.append((tenant, wd, site, n, total))
                print(f"  ✓ {tenant}.{wd} [{site}]: {n} jobs (total: {total})")
            else:
                # Site was found via redirect but returned no jobs — still record it
                found.append((tenant, wd, site, 0, 0))
                print(f"  - {tenant}.{wd} [{site}]: 0 jobs (site found but no postings)")

    print(f"\n=== Active Workday tenants: {len(found)} ===")
    found.sort(key=lambda x: -x[4])
    for tenant, wd, site, n, total in found:
        print(f"  {tenant}.{wd} [{site}]: {n} jobs, total={total}")

    with open("/tmp/workday_active.json", "w") as f:
        json.dump(
            [{"tenant": t, "wd": w, "site": s, "jobs": n, "total": total}
             for t, w, s, n, total in found],
            f,
            indent=2,
        )
    print("\nWrote /tmp/workday_active.json")


if __name__ == "__main__":
    asyncio.run(main())
