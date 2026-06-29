"""
Generic Career Page Scraper

For companies with custom career pages (not using Greenhouse/Lever/Ashby/Workable),
we scrape the page and look for JSON-LD JobPosting schema or structured job cards.

This is the "all angles" fallback: if a user pastes any company career URL,
we attempt to extract jobs from it.
"""

from typing import List, Dict, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse

from .base import BaseScraper, JobData


class CareerPageScraper(BaseScraper):
    """Scrape any company career page for job listings via JSON-LD or HTML parsing."""

    name = "career_page"

    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        """Treat company_subdomain as a full URL."""
        if not company_subdomain.startswith(("http://", "https://")):
            url = f"https://{company_subdomain}"
        else:
            url = company_subdomain
        return await self.scrape_url(url)

    async def scrape_url(self, url: str) -> List[JobData]:
        """Scrape a career page URL for job postings."""
        html = await self.fetch(url)
        if not html:
            return []
        return self._parse_html(html, url)

    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        return []

    async def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        max_jobs: int = 50,
    ) -> List[JobData]:
        # Career page scraper needs a URL — not used for keyword search
        return []

    def _parse_html(self, html: str, base_url: str) -> List[JobData]:
        soup = BeautifulSoup(html, "lxml")
        results: List[JobData] = []

        # 1. Look for JSON-LD JobPosting objects (Schema.org)
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string or "{}")
            except (ValueError, TypeError):
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                # Item can be a single JobPosting or an ItemList of JobPostings
                if item.get("@type") == "ItemList":
                    graph = item.get("itemListElement") or []
                    for el in graph:
                        if isinstance(el, dict):
                            inner = el.get("item") or el
                            if isinstance(inner, dict) and inner.get("@type") in ("JobPosting", ["JobPosting"]):
                                try:
                                    results.append(self._parse_jsonld(inner, base_url))
                                except Exception:
                                    continue
                elif item.get("@type") in ("JobPosting", ["JobPosting"]):
                    try:
                        results.append(self._parse_jsonld(item, base_url))
                    except Exception:
                        continue
                elif "@graph" in item:
                    for g in item.get("@graph") or []:
                        if isinstance(g, dict) and g.get("@type") in ("JobPosting", ["JobPosting"]):
                            try:
                                results.append(self._parse_jsonld(g, base_url))
                            except Exception:
                                continue

        if results:
            return results

        # 2. Fall back to HTML job card heuristics
        # Common patterns: <a class="job-card">, <li class="posting">, etc.
        candidates = []
        for selector in [
            "a[class*='job']", "div[class*='job-card']", "div[class*='jobCard']",
            "li[class*='job']", "article[class*='job']",
            "[data-job-id]", "[data-testid*='job']",
        ]:
            candidates.extend(soup.select(selector))

        seen_ids = set()
        for card in candidates:
            try:
                link = card if card.name == "a" else card.find("a")
                if not link:
                    continue
                href = link.get("href") or ""
                if not href or href == "#":
                    continue
                title = link.get_text(strip=True) or card.get_text(strip=True)[:200]
                if not title or len(title) < 3:
                    continue
                url = urljoin(base_url, href)
                ext_id = f"career_{hash(url)}"
                if ext_id in seen_ids:
                    continue
                seen_ids.add(ext_id)
                results.append(JobData(
                    title=title,
                    company=self._extract_company_name(soup, base_url),
                    location="",
                    external_id=ext_id,
                    external_url=url,
                    description="",
                    seniority=self.parse_seniority(title),
                    raw_data={"source": "career_page", "title": title},
                ))
            except Exception:
                continue

        return results

    def _parse_jsonld(self, item: Dict, base_url: str) -> JobData:
        title = item.get("title") or "Unknown Position"
        org = item.get("hiringOrganization") or {}
        company = ""
        if isinstance(org, dict):
            company = org.get("name") or ""
        elif isinstance(org, str):
            company = org
        if not company:
            company = self._extract_company_name(BeautifulSoup("", "lxml"), base_url)

        # Location
        location = ""
        loc_obj = item.get("jobLocation") or item.get("jobLocationType")
        if isinstance(loc_obj, dict):
            addr = loc_obj.get("address") or {}
            if isinstance(addr, dict):
                parts = [addr.get("streetAddress"), addr.get("addressLocality"),
                         addr.get("addressRegion"), addr.get("addressCountry")]
                location = ", ".join([p for p in parts if p])
            else:
                location = str(addr)
        elif isinstance(loc_obj, str):
            location = loc_obj

        # Remote / hybrid
        remote = item.get("jobLocationType") == "TELECOMMUTE" or "remote" in location.lower()
        hybrid = "hybrid" in location.lower()

        # Dates
        posted = self._parse_date(item.get("datePosted"))
        valid_through = self._parse_date(item.get("validThrough"))

        # Salary
        min_salary = None
        max_salary = None
        salary = item.get("baseSalary") or {}
        if isinstance(salary, dict):
            value = salary.get("value") or {}
            if isinstance(value, dict):
                try:
                    if value.get("minValue"):
                        min_salary = int(float(value["minValue"]))
                    if value.get("maxValue"):
                        max_salary = int(float(value["maxValue"]))
                except (ValueError, TypeError):
                    pass

        url = item.get("url") or ""
        if url and not url.startswith(("http://", "https://")):
            url = urljoin(base_url, url)

        return JobData(
            title=title,
            company=company,
            location=location,
            external_id=str(item.get("identifier") or item.get("@id") or f"career_{hash(url)}"),
            external_url=url,
            description=item.get("description") or "",
            remote=remote,
            hybrid=hybrid,
            min_salary=min_salary,
            max_salary=max_salary,
            employment_type=item.get("employmentType"),
            posted_date=posted,
            raw_data=item,
        )

    def _extract_company_name(self, soup: BeautifulSoup, base_url: str) -> str:
        # Try meta tags
        og_site = soup.find("meta", property="og:site_name")
        if og_site and og_site.get("content"):
            return og_site["content"]
        # Fall back to domain
        try:
            host = urlparse(base_url).netloc
            return host.split(":")[0].replace("www.", "")
        except Exception:
            return "Unknown"

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None