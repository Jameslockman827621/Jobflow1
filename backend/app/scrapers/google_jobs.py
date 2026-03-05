"""
Google Jobs Scraper

Scrapes job listings from Google Jobs search results.
Google aggregates jobs from multiple sources including LinkedIn.

URL pattern: https://www.google.com/search?q=jobs&ibp=htl;jobs

Note: This uses HTML scraping. For production, consider:
- Google Custom Search API (paid, legitimate)
- SERP API services (serpapi.com, etc.)
"""

from typing import List, Optional, Dict
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import urllib.parse

from .base import BaseScraper, JobData


class GoogleJobsScraper(BaseScraper):
    name = "google_jobs"
    base_url = "https://www.google.com/search"
    
    def __init__(self):
        super().__init__()
        self.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
    
    async def search_jobs(
        self,
        query: str,
        location: Optional[str] = None,
        remote: bool = False,
        limit: int = 50,
    ) -> List[JobData]:
        """Search Google Jobs"""
        # Build search query
        search_query = f"{query} jobs"
        if location:
            search_query += f" in {location}"
        if remote:
            search_query += " remote"
        
        params = {
            "q": search_query,
            "ibp": "htl;jobs",  # Jobs filter
            "num": limit,
        }
        
        url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
        
        html = await self.fetch(url)
        if not html:
            return []
        
        return self._parse_results(html)
    
    async def scrape_company_jobs(self, company_name: str) -> List[JobData]:
        """Scrape jobs for a specific company"""
        return await self.search_jobs(f"{company_name}", limit=50)
    
    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        """Scrape generic jobs (not company-specific)"""
        return await self.search_jobs("", limit=limit)
    
    def _parse_results(self, html: str) -> List[JobData]:
        """Parse Google Jobs search results"""
        soup = BeautifulSoup(html, 'lxml')
        jobs = []
        
        # Google Jobs uses specific data attributes
        # Note: Google frequently changes their HTML structure
        job_cards = soup.select('div[data-job-title], div[jsname], .job_card')
        
        for card in job_cards[:50]:  # Limit parsing
            try:
                title_elem = card.select_one('[data-job-title], h2, .job-title')
                company_elem = card.select_one('[data-company-name], .company-name, span:nth-child(2)')
                location_elem = card.select_one('[data-location], .location, span:nth-child(3)')
                link_elem = card.select_one('a[href*="/search?q="], a.job-link')
                
                title = title_elem.get_text(strip=True) if title_elem else None
                if not title:
                    continue  # Skip if no title
                
                company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                location = location_elem.get_text(strip=True) if location_elem else ""
                link = link_elem.get('href') if link_elem else ""
                
                # Clean up Google's redirect URL
                if link and 'google.com/url' in link:
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(link)
                    params = parse_qs(parsed.query)
                    if 'url' in params:
                        link = params['url'][0]
                
                # Detect remote
                remote = 'remote' in location.lower() or 'work from home' in title.lower()
                
                job = JobData(
                    title=title,
                    company=company,
                    location=location,
                    external_id=f"google_{hash(link)}",
                    external_url=link,
                    description="",  # Would need to fetch individual pages
                    remote=remote,
                    hybrid='hybrid' in location.lower(),
                    seniority=self.parse_seniority(title),
                    raw_data={"source": "google_jobs"},
                )
                jobs.append(job)
                
            except Exception as e:
                print(f"Error parsing job card: {e}")
                continue
        
        print(f"  Google Jobs: Found {len(jobs)} jobs")
        return jobs


# Test function
if __name__ == "__main__":
    import asyncio
    
    async def test():
        scraper = GoogleJobsScraper()
        jobs = await scraper.search_jobs("software engineer", location="London", remote=True, limit=20)
        print(f"Found {len(jobs)} jobs")
        for job in jobs[:5]:
            print(f"  - {job.title} at {job.company} ({job.location})")
    
    asyncio.run(test())
