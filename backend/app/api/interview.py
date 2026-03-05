from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.core.security import get_current_user
from app.models.user import User
from app.services.interview_prep import interview_prep

router = APIRouter()


class InterviewPrepRequest(BaseModel):
    role: str
    company: Optional[str] = None
    seniority: Optional[str] = None
    tech_stack: Optional[List[str]] = None


class InterviewPrepResponse(BaseModel):
    technical: List[str]
    behavioral: List[str]
    company_specific: List[str]
    tips: List[str]
    company_research: dict


@router.post("/generate", response_model=InterviewPrepResponse)
async def generate_interview_prep(
    request: InterviewPrepRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate interview questions and prep materials"""
    questions = interview_prep.generate_questions(
        role=request.role,
        company=request.company,
        seniority=request.seniority,
        tech_stack=request.tech_stack,
    )
    
    company_research = {}
    if request.company:
        company_research = interview_prep.generate_company_research(request.company)
    
    return InterviewPrepResponse(
        technical=questions["technical"],
        behavioral=questions["behavioral"],
        company_specific=questions["company_specific"],
        tips=questions["tips"],
        company_research=company_research,
    )


@router.get("/tips/{role}")
async def get_role_tips(
    role: str,
    current_user: User = Depends(get_current_user),
):
    """Get interview tips for a specific role"""
    tips = interview_prep._get_prep_tips(role, None)
    return {"role": role, "tips": tips}
