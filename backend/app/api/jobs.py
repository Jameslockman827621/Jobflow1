from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from app.models.job import Job

router = APIRouter()


class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: str
    remote: bool
    external_url: str
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    seniority: Optional[str] = None
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    search: Optional[str] = Query(None, description="Search in title/company"),
    location: Optional[str] = Query(None),
    remote: Optional[bool] = Query(None),
    min_salary: Optional[int] = Query(None),
    seniority: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    """
    List jobs with filters.
    TODO: Implement actual DB query with filters.
    """
    # Placeholder
    return []


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int):
    """Get a specific job by ID"""
    # TODO: Implement
    raise HTTPException(status_code=404, detail="Job not found")


@router.post("/scrape/{source}")
async def trigger_scrape(source: str):
    """
    Trigger job scraping for a source.
    Sources: greenhouse, lever, workable
    """
    # TODO: Implement with Celery task
    return {"status": "scrape started", "source": source}
