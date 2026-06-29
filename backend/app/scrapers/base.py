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
        employment_type: Optional[str] = None,
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
        self.employment_type = employment_type
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
            "employment_type": self.employment_type,
            "posted_date": self.posted_date.isoformat() if self.posted_date else None,
        }


class BaseScraper(ABC):
    """Base class for all job scrapers"""

    name: str = "base"
    base_url: str = ""

    def __init__(self):
        try:
            self.ua = UserAgent()
            user_agent = self.ua.random
        except Exception:
            user_agent = (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def fetch(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: float = 30.0,
    ) -> Optional[str]:
        """Fetch URL with basic rate limiting"""
        merged_headers = {**self.headers, **(headers or {})}
        async with httpx.AsyncClient(
            headers=merged_headers,
            timeout=timeout,
            follow_redirects=True,
        ) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.text
            except httpx.HTTPError as e:
                print(f"Error fetching {url}: {e}")
                return None

    async def fetch_json(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: float = 30.0,
    ) -> Optional[Dict]:
        """Fetch URL and parse JSON response"""
        merged_headers = {**self.headers, **(headers or {})}
        merged_headers.setdefault("Accept", "application/json")
        async with httpx.AsyncClient(
            headers=merged_headers,
            timeout=timeout,
            follow_redirects=True,
        ) as client:
            try:
                response = await client.get(url, params=params)
                if response.status_code >= 400:
                    return None
                return response.json()
            except (httpx.HTTPError, ValueError) as e:
                print(f"Error fetching JSON from {url}: {e}")
                return None

    async def post_json(
        self,
        url: str,
        json_body: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: float = 30.0,
    ) -> Optional[Dict]:
        """POST JSON and parse JSON response"""
        merged_headers = {**self.headers, **(headers or {})}
        merged_headers.setdefault("Accept", "application/json")
        async with httpx.AsyncClient(
            headers=merged_headers,
            timeout=timeout,
            follow_redirects=True,
        ) as client:
            try:
                response = await client.post(url, json=json_body)
                if response.status_code >= 400:
                    return None
                return response.json()
            except (httpx.HTTPError, ValueError) as e:
                print(f"Error POSTing to {url}: {e}")
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

        # Normalize "k" suffix (e.g. 90k -> 90000)
        cleaned = re.sub(r'[,$£€]', '', salary_text.lower())
        numbers_with_k = re.findall(r'(\d+(?:\.\d+)?)\s*k', cleaned)
        if numbers_with_k:
            values = [int(float(n) * 1000) for n in numbers_with_k]
            if len(values) >= 2:
                return min(values), max(values)
            elif len(values) == 1:
                return None, values[0]

        numbers = re.findall(r'\d+(?:\.\d+)?', cleaned)
        if len(numbers) >= 2:
            return int(float(numbers[0])), int(float(numbers[1]))
        elif len(numbers) == 1:
            return None, int(float(numbers[0]))

        return None, None

    def parse_seniority(self, title: str) -> Optional[str]:
        """Extract seniority level from job title"""
        if not title:
            return "mid"
        title_lower = title.lower()

        if any(x in title_lower for x in ["executive", "c-level", "cto", "ceo", "cfo", "chief"]):
            return "executive"
        elif any(x in title_lower for x in ["vp", "vice president", "head of"]):
            return "executive"
        elif any(x in title_lower for x in ["director"]):
            return "director"
        elif any(x in title_lower for x in ["lead", "principal", "staff"]):
            return "lead"
        elif any(x in title_lower for x in ["senior", "sr.", "sr ", "snr"]):
            return "senior"
        elif any(x in title_lower for x in ["junior", "jr.", "jr ", "entry", "graduate", "intern"]):
            return "entry"
        else:
            return "mid"

    def parse_employment_type(self, text: str) -> Optional[str]:
        """Detect employment type from text"""
        if not text:
            return None
        t = text.lower()
        if "full-time" in t or "full time" in t or "fulltime" in t:
            return "FULL_TIME"
        if "part-time" in t or "part time" in t or "parttime" in t:
            return "PART_TIME"
        if "contract" in t or "contractor" in t:
            return "CONTRACT"
        if "intern" in t:
            return "INTERN"
        if "temporary" in t or "temp" in t:
            return "TEMPORARY"
        return None

    def parse_posted_date(self, text: str) -> Optional[datetime]:
        """Parse relative date strings like '2 days ago', '1 week ago'"""
        from datetime import timedelta
        import re
        if not text:
            return None
        t = text.lower()
        m = re.search(r'(\d+)\s*(day|week|month|hour|minute)s?\s*ago', t)
        if m:
            n = int(m.group(1))
            unit = m.group(2)
            now = datetime.utcnow()
            if unit == "minute":
                return now - timedelta(minutes=n)
            if unit == "hour":
                return now - timedelta(hours=n)
            if unit == "day":
                return now - timedelta(days=n)
            if unit == "week":
                return now - timedelta(weeks=n)
            if unit == "month":
                return now - timedelta(days=n * 30)
        return None
