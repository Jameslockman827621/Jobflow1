"""
AI Interview Coach API

Simulates real interviews with:
- Role-specific questions
- Follow-up questions based on answers
- Real-time feedback
- Scoring and improvement tips

Uses streaming for conversational experience.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import asyncio

from app.core.security import get_current_user
from app.models.user import User
from app.core.config import settings

router = APIRouter()


class InterviewSession(BaseModel):
    role: str
    company: Optional[str] = None
    seniority: str = "mid"
    duration_minutes: int = 30
    focus_areas: Optional[List[str]] = None  # ["technical", "behavioral", "system_design"]


class InterviewMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: float


class InterviewFeedback(BaseModel):
    overall_score: int  # 1-10
    categories: Dict[str, int]  # category -> score
    strengths: List[str]
    improvements: List[str]
    tips: List[str]


# Mock interview questions database (would use AI in production)
INTERVIEW_FLOWS = {
    "software engineer": {
        "technical": [
            "Tell me about a challenging technical problem you solved. What was your approach?",
            "How would you design a URL shortening service like bit.ly?",
            "Explain how you'd optimize a slow database query.",
        ],
        "behavioral": [
            "Describe a time you disagreed with a teammate. How did you handle it?",
            "Tell me about a project that didn't go as planned.",
        ],
        "system_design": [
            "Design Twitter's feed system.",
            "How would you build a real-time chat application?",
        ],
    },
    "product manager": {
        "product_sense": [
            "How would you improve [Product X]?",
            "What metrics would you track for this feature?",
        ],
        "leadership": [
            "Tell me about a time you influenced without authority.",
        ],
    },
}


@router.post("/start")
async def start_interview(
    session: InterviewSession,
    current_user: User = Depends(get_current_user),
):
    """Start a new mock interview session"""
    # In production, this would create a session in Redis/DB
    # and initialize an AI conversation
    
    session_id = f"interview_{current_user.id}_{asyncio.get_event_loop().time()}"
    
    # Get initial question based on role
    role_lower = session.role.lower()
    questions = INTERVIEW_FLOWS.get(role_lower, INTERVIEW_FLOWS["software engineer"])
    
    # Pick first technical question
    initial_question = questions.get("technical", ["Tell me about yourself."])[0]
    
    return {
        "session_id": session_id,
        "role": session.role,
        "initial_question": initial_question,
        "duration_minutes": session.duration_minutes,
        "focus_areas": session.focus_areas or ["technical", "behavioral"],
    }


@router.post("/{session_id}/message")
async def send_message(
    session_id: str,
    message: str,
    current_user: User = Depends(get_current_user),
):
    """Send a message in the interview (user's answer)"""
    # In production, this would:
    # 1. Send user's answer to AI
    # 2. Get AI's evaluation and follow-up question
    # 3. Return follow-up + real-time feedback
    
    # Mock response for now
    follow_up_questions = [
        "That's interesting. Can you go deeper into the technical tradeoffs?",
        "How did you measure the success of that approach?",
        "What would you do differently if you had more time?",
        "Can you explain that to someone without a technical background?",
    ]
    
    import random
    follow_up = random.choice(follow_up_questions)
    
    return {
        "follow_up_question": follow_up,
        "feedback": {
            "clarity": 7,
            "technical_depth": 6,
            "structure": 8,
        },
        "is_complete": False,
    }


@router.post("/{session_id}/end")
async def end_interview(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """End interview and get detailed feedback"""
    # In production, AI would analyze the full conversation
    
    return InterviewFeedback(
        overall_score=7,
        categories={
            "technical_knowledge": 7,
            "communication": 8,
            "problem_solving": 6,
            "cultural_fit": 8,
        },
        strengths=[
            "Clear communication style",
            "Good use of specific examples",
            "Demonstrated leadership experience",
        ],
        improvements=[
            "Go deeper into technical tradeoffs",
            "Quantify impact more (use numbers)",
            "Prepare more system design examples",
        ],
        tips=[
            "Practice the STAR method for behavioral questions",
            "Review system design fundamentals",
            "Prepare 2-3 backup stories for common questions",
        ],
    ).dict()


@router.get("/questions/{role}")
async def get_practice_questions(
    role: str,
    current_user: User = Depends(get_current_user),
):
    """Get practice questions for a role"""
    role_lower = role.lower()
    questions = INTERVIEW_FLOWS.get(role_lower, INTERVIEW_FLOWS["software engineer"])
    
    return {
        "role": role,
        "questions": questions,
    }


@router.post("/evaluate-answer")
async def evaluate_answer(
    question: str,
    answer: str,
    current_user: User = Depends(get_current_user),
):
    """Get AI evaluation of a practice answer"""
    # In production, send to LLM for evaluation
    
    # Mock evaluation
    return {
        "score": 7,
        "feedback": "Good answer! You covered the main points. To improve: add more specific metrics and discuss alternative approaches you considered.",
        "suggested_improvements": [
            "Add quantifiable results",
            "Mention tradeoffs considered",
            "Include what you learned",
        ],
    }
