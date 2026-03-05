"""
Lever ATS Scraper

Lever powers 10,000+ company career pages.
URL pattern: https://hire.lever.co/postings/{company}
API is public for embedding.
"""

from typing import List, Dict
from datetime import datetime
import httpx
import re

from .base import BaseScraper, JobData


class LeverScraper(BaseScraper):
    name = "lever"
    base_url = "https://hire.lever.co/postings"
    
    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        """Scrape jobs for a specific company"""
        url = f"{self.base_url}/{company_subdomain}"
        
        async with httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True,
        ) as client:
            try:
                response = await client.get(url)
                if response.status_code == 404:
                    print(f"  {company_subdomain}: Not on Lever")
                    return []
                response.raise_for_status()
                html = response.text
                
                # Parse HTML to extract job data
                # Lever returns HTML with embedded JSON in data attributes
                jobs = self._parse_lever_html(html, company_subdomain)
                print(f"  {company_subdomain}: Found {len(jobs)} jobs")
                return jobs
            except httpx.HTTPStatusError as e:
                print(f"HTTP error for {company_subdomain}: {e.response.status_code}")
                return []
            except Exception as e:
                print(f"Error scraping {company_subdomain}: {e}")
                return []
    
    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        """Lever doesn't have global search - needs company list"""
        print("Lever: scrape_all_jobs not implemented - needs company list")
        return []
    
    def _parse_lever_html(self, html: str, company: str) -> List[JobData]:
        """Parse Lever HTML response to extract job postings"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'lxml')
        jobs = []
        
        # Find all job posting links
        job_links = soup.select('ul.postings li.posting')
        
        for li in job_links:
            try:
                title_elem = li.select_one('a')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                href = title_elem.get('href', '')
                
                # Get location/department from spans
                meta_spans = li.select('span')
                location = ""
                department = ""
                
                for span in meta_spans:
                    text = span.get_text(strip=True)
                    if 'location' in span.get('class', []) or 'location' in text.lower():
                        location = text
                    elif 'department' in span.get('class', []):
                        department = text
                
                # If no class-based detection, use order (Lever typically: department • location)
                if not location and len(meta_spans) >= 2:
                    parts = [s.get_text(strip=True) for s in meta_spans[:2]]
                    if len(parts) == 2:
                        department, location = parts
                
                # Clean up location (remove • separators)
                location = location.replace('•', '').strip()
                
                remote = "remote" in location.lower() if location else False
                hybrid = "hybrid" in location.lower() if location else False
                
                job = JobData(
                    title=title,
                    company=company,
                    location=location,
                    external_id=href.split('/')[-1] if href else "",
                    external_url=href if href.startswith('http') else f"https://hire.lever.co{href}",
                    description="",  # Would need to fetch individual job pages
                    remote=remote,
                    hybrid=hybrid,
                    department=department if department else None,
                    seniority=self.parse_seniority(title),
                    raw_data={"html_class": "lever_posting"},
                )
                jobs.append(job)
            except Exception as e:
                print(f"Error parsing job element: {e}")
                continue
        
        return jobs
    
    def _parse_job(self, job: Dict, company: str) -> JobData:
        """Parse Lever job API response (legacy, kept for compatibility)"""
        location = ""
        remote = False
        hybrid = False
        
        location_data = job.get("locations", {})
        if isinstance(location_data, list):
            location = location_data[0] if location_data else ""
        else:
            location = location_data.get("text", "") if location_data else ""
        
        remote = "remote" in location.lower() if location else False
        hybrid = "hybrid" in location.lower() if location else False
        
        department = job.get("departments", [{}])[0].get("text") if job.get("departments") else None
        
        return JobData(
            title=job.get("title", ""),
            company=company,
            location=location,
            external_id=job.get("id", ""),
            external_url=job.get("hostedUrl", ""),
            description=job.get("description", ""),
            remote=remote,
            hybrid=hybrid,
            department=department,
            seniority=self.parse_seniority(job.get("title", "")),
            posted_date=datetime.fromisoformat(job["updatedAt"].replace("Z", "+00:00")) if job.get("updatedAt") else None,
            raw_data=job,
        )
