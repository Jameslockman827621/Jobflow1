#!/usr/bin/env python3
"""
Manually scrape jobs from configured companies.
Useful for testing the scrapers.
"""

import asyncio
import sys
sys.path.insert(0, "..")

from app.scrapers import GreenhouseScraper, LeverScraper
from app.scrapers.companies import GREENHOUSE_COMPANIES, LEVER_COMPANIES


async def scrape_greenhouse():
    print("Scraping Greenhouse companies...")
    scraper = GreenhouseScraper()
    
    total_jobs = 0
    for company in GREENHOUSE_COMPANIES[:5]:  # Limit to first 5 for testing
        jobs = await scraper.scrape_company_jobs(company)
        total_jobs += len(jobs)
        print(f"  {company}: {len(jobs)} jobs")
    
    print(f"\nTotal: {total_jobs} jobs from {len(GREENHOUSE_COMPANIES[:5])} companies")


async def scrape_lever():
    print("Scraping Lever companies...")
    scraper = LeverScraper()
    
    total_jobs = 0
    for company in LEVER_COMPANIES[:5]:  # Limit to first 5 for testing
        jobs = await scraper.scrape_company_jobs(company)
        total_jobs += len(jobs)
        print(f"  {company}: {len(jobs)} jobs")
    
    print(f"\nTotal: {total_jobs} jobs from {len(LEVER_COMPANIES[:5])} companies")


async def main():
    print("=== JobScale Job Scraper Test ===\n")
    
    await scrape_greenhouse()
    print()
    await scrape_lever()
    
    print("\n✓ Scraping test complete!")


if __name__ == "__main__":
    asyncio.run(main())
