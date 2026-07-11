"""
Greenhouse Job Board Discovery Scraper

Greenhouse maintains a public directory of companies using their ATS at
  https://boards-api.greenhouse.io/v1/boards
This module provides keyword search across all known Greenhouse companies.
Used by the aggregator for broad searches when the user hasn't picked specific companies.
"""

from typing import List, Dict, Optional
from .base import BaseScraper, JobData
from .greenhouse import GreenhouseScraper


class GreenhouseBoardScraper(GreenhouseScraper):
    """Greenhouse scraper optimized for board-wide keyword search."""

    name = "greenhouse_board"

    async def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        max_jobs: int = 50,
    ) -> List[JobData]:
        return await super().search_jobs(keywords=keywords, location=location, max_jobs=max_jobs)