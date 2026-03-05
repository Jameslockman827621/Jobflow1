from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.job import Job, JobSource

router = APIRouter()


class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: str
    remote: bool
    hybrid: bool
    external_url: str
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    seniority: Optional[str] = None
    department: Optional[str] = None
    posted_date: Optional[str] = None
    match_score: Optional[float] = None
    
    class Config:
        from_attributes = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    search: Optional[str] = Query(None, description="Search in title/company"),
    location: Optional[str] = Query(None),
    remote: Optional[bool] = Query(None),
    min_salary: Optional[int] = Query(None),
    seniority: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List jobs with filters"""
    query = db.query(Job).filter(Job.is_active == True)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Job.title.ilike(search_term),
                Job.company.ilike(search_term),
            )
        )
    
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    
    if remote is not None:
        query = query.filter(Job.remote == remote)
    
    if min_salary is not None:
        query = query.filter(
            or_(
                Job.max_salary >= min_salary,
                Job.min_salary >= min_salary,
            )
        )
    
    if seniority:
        query = query.filter(Job.seniority == seniority)
    
    # Order by most recent
    query = query.order_by(Job.created_at.desc())
    
    # Pagination
    jobs = query.offset(offset).limit(limit).all()
    
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a specific job by ID"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/scrape/{source}")
async def trigger_scrape(source: str, db: Session = Depends(get_db)):
    """
    Trigger job scraping for a source.
    Sources: greenhouse, lever, workable
    """
    from app.tasks.jobs import scrape_greenhouse_companies, scrape_lever_companies
    from app.scrapers.companies import GREENHOUSE_COMPANIES, LEVER_COMPANIES
    
    if source == "greenhouse":
        scrape_greenhouse_companies.delay(GREENHOUSE_COMPANIES)
        return {"status": "scrape started", "source": source, "companies": len(GREENHOUSE_COMPANIES)}
    elif source == "lever":
        scrape_lever_companies.delay(LEVER_COMPANIES)
        return {"status": "scrape started", "source": source, "companies": len(LEVER_COMPANIES)}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown source: {source}")


@router.get("/sources")
async def list_sources(db: Session = Depends(get_db)):
    """List all job sources"""
    sources = db.query(JobSource).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "base_url": s.base_url,
            "is_active": s.is_active,
            "last_scraped": s.last_scraped.isoformat() if s.last_scraped else None,
        }
        for s in sources
    ]
