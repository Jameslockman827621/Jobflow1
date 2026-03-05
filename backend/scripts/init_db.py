#!/usr/bin/env python3
"""
Initialize the database with job sources and sample data.
Run this after starting the database.
"""

import sys
sys.path.insert(0, "..")

from app.database import init_db, SessionLocal
from app.models.job import JobSource
from app.models.user import User
from app.models.profile import UserProfile

def main():
    print("Initializing database...")
    
    # Create tables
    init_db()
    print("✓ Tables created")
    
    # Create job sources
    db = SessionLocal()
    try:
        sources = [
            {"name": "greenhouse", "base_url": "https://boards-api.greenhouse.io/v1/boards"},
            {"name": "lever", "base_url": "https://api.lever.co/v0/postings"},
            {"name": "workable", "base_url": "https://www.workable.com/api/v2/jobs"},
        ]
        
        for source_data in sources:
            source, created = db.query(JobSource).filter_by(name=source_data["name"]).first_or_create(
                defaults=source_data
            )
            if created:
                print(f"✓ Created job source: {source_data['name']}")
        
        db.commit()
        print("✓ Job sources initialized")
        
    finally:
        db.close()
    
    print("\nDatabase initialization complete!")
    print("\nNext steps:")
    print("1. Start the backend: cd backend && uvicorn app.main:app --reload")
    print("2. Start Celery worker: celery -A app.tasks.celery_app worker --loglevel=info")
    print("3. Trigger job scraping: POST /api/v1/jobs/scrape/greenhouse")
    print("4. Open API docs: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
