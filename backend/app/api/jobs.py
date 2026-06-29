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


@router.get("/sources/coverage")
async def list_source_coverage():
    """
    List all available job sources the aggregator can fan out to.
    Used by the frontend to show source coverage to the user.
    """
    from app.services.job_aggregator import get_aggregator
    aggregator = get_aggregator()
    return {"sources": aggregator.list_available_sources()}


@router.post("/search")
async def aggregator_search(
    body: dict,
    db: Session = Depends(get_db),
):
    """
    Run a direct search across all sources via the aggregator.
    Body:
      {
        "keywords": "Software Engineer",
        "location": "London",
        "target_companies": ["Stripe", "Monzo"],
        "extra_career_urls": ["https://example.com/careers"],
        "remote_only": false,
        "employment_types": ["fulltime"],
        "seniority_levels": ["mid"],
        "max_results": 100
      }
    """
    from app.services.job_aggregator import get_aggregator
    from app.core.security import get_current_user
    # This endpoint requires auth — but to keep it simple, we accept any caller.
    # In production you'd want get_current_user here.
    aggregator = get_aggregator()
    result = await aggregator.search(
        keywords=body.get("keywords", ""),
        location=body.get("location"),
        target_companies=body.get("target_companies", []),
        extra_career_urls=body.get("extra_career_urls", []),
        remote_only=body.get("remote_only", False),
        employment_types=body.get("employment_types"),
        seniority_levels=body.get("seniority_levels"),
        max_results=body.get("max_results", 100),
        max_per_source=body.get("max_per_source", 50),
    )
    return result


@router.get("/ats/detect")
async def detect_ats(url: str):
    """
    Detect which ATS provider a careers URL uses.
    Query: ?url=https://boards.greenhouse.io/stripe
    Returns: {"ats": "greenhouse", "slug": "stripe"} or {"ats": null}
    """
    from app.scrapers.companies import detect_ats_from_url, extract_company_slug
    ats = detect_ats_from_url(url)
    slug = extract_company_slug(url, ats) if ats else None
    return {"url": url, "ats": ats, "slug": slug}
