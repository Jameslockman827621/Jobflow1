from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    status: str
    stage: str
    submitted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CreateApplication(BaseModel):
    job_id: int


@router.get("/", response_model=List[ApplicationResponse])
async def list_applications():
    """List all applications for current user"""
    # TODO: Implement
    return []


@router.post("/", response_model=ApplicationResponse)
async def create_application(data: CreateApplication):
    """Create a new application for a job"""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.patch("/{app_id}")
async def update_application(app_id: int, status: Optional[str] = None, notes: Optional[str] = None):
    """Update application status or notes"""
    # TODO: Implement
    return {"status": "updated"}


@router.post("/{app_id}/apply")
async def submit_application(app_id: int):
    """
    Submit an application - triggers AI to tailor CV and cover letter.
    TODO: Implement AI integration.
    """
    raise HTTPException(status_code=501, detail="Not implemented")
