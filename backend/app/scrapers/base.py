from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime
import httpx
from fake_useragent import UserAgent

from app.core.config import settings


class JobData:
    """Normalized job data structure"""
    def __init__(
        self,
        title: str,
        company: str,
        location: str,
        external_id: str,
        external_url: str,
        description: str = "",
        remote: bool = False,
        hybrid: bool = False,
        min_salary: Optional[int] = None,
        max_salary: Optional[int] = None,
        department: Optional[str] = None,
        seniority: Optional[str] = None,
        posted_date: Optional[datetime] = None,
        raw_data: Optional[Dict] = None,
    ):
        self.title = title
        self.company = company
        self.location = location
        self.external_id = external_id
        self.external_url = external_url
        self.description = description
        self.remote = remote
        self.hybrid = hybrid
        self.min_salary = min_salary
        self.max_salary = max_salary
        self.department = department
        self.seniority = seniority
        self.posted_date = posted_date
        self.raw_data = raw_data
    
    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "external_id": self.external_id,
            "external_url": self.external_url,
            "description": self.description,
            "remote": self.remote,
            "hybrid": self.hybrid,
            "min_salary": self.min_salary,
            "max_salary": self.max_salary,
            "department": self.department,
            "seniority": self.seniority,
            "posted_date": self.posted_date.isoformat() if self.posted_date else None,
        }


class BaseScraper(ABC):
    """Base class for all job scrapers"""
    
    name: str = "base"
    base_url: str = ""
    
    def __init__(self):
        self.ua = UserAgent()
        self.headers = {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
    
    async def fetch(self, url: str, params: Optional[Dict] = None) -> Optional[str]:
        """Fetch URL with basic rate limiting"""
        async with httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True,
        ) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.text
            except httpx.HTTPError as e:
                print(f"Error fetching {url}: {e}")
                return None
    
    @abstractmethod
    async def scrape_company_jobs(self, company_subdomain: str) -> List[JobData]:
        """Scrape all jobs for a specific company"""
        pass
    
    @abstractmethod
    async def scrape_all_jobs(self, limit: int = 100) -> List[JobData]:
        """Scrape jobs across all companies (if supported)"""
        pass
    
    def parse_salary(self, salary_text: str) -> tuple[Optional[int], Optional[int]]:
        """Extract min/max salary from text"""
        import re
        if not salary_text:
            return None, None
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[,$£€]', '', salary_text)
        
        # Find numbers
        numbers = re.findall(r'\d+(?:\.\d+)?', cleaned)
        if len(numbers) >= 2:
            return int(float(numbers[0])), int(float(numbers[1]))
        elif len(numbers) == 1:
            return None, int(float(numbers[0]))
        
        return None, None
    
    def parse_seniority(self, title: str) -> Optional[str]:
        """Extract seniority level from job title"""
        title_lower = title.lower()
        
        if any(x in title_lower for x in ["executive", "c-level", "cto", "ceo", "cfo"]):
            return "executive"
        elif any(x in title_lower for x in ["vp", "vice president"]):
            return "executive"
        elif any(x in title_lower for x in ["director", "head of"]):
            return "lead"
        elif any(x in title_lower for x in ["senior", "sr.", "sr "]):
            return "senior"
        elif any(x in title_lower for x in ["junior", "jr.", "jr ", "entry", "graduate"]):
            return "entry"
        elif any(x in title_lower for x in ["lead", "principal", "staff"]):
            return "lead"
        else:
            return "mid"
