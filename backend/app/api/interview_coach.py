"""
AI Interview Coach API — real LLM only (no fake scores).
"""

from __future__ import annotations

import json
import time
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAI
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


class InterviewSession(BaseModel):
    role: str
    company: Optional[str] = None
    seniority: str = "mid"
    duration_minutes: int = 30
    focus_areas: Optional[List[str]] = None


class InterviewFeedback(BaseModel):
    overall_score: int
    categories: Dict[str, int]
    strengths: List[str]
    improvements: List[str]
    tips: List[str]


def _client() -> OpenAI:
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured — interview coach disabled (no mock scores).",
        )
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def _chat(system: str, user: str, *, max_tokens: int = 800) -> str:
    client = _client()
    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=0.4,
    )
    return (resp.choices[0].message.content or "").strip()


@router.post("/start")
async def start_interview(
    session: InterviewSession,
    current_user: User = Depends(get_current_user),
):
    """Start a new interview session with a real LLM opening question."""
    _ = current_user
    prompt = (
        f"You are a tough but fair interviewer for a {session.seniority} {session.role} role"
        + (f" at {session.company}" if session.company else "")
        + f". Focus areas: {', '.join(session.focus_areas or ['technical', 'behavioral'])}. "
        "Ask ONE opening interview question only. No preamble."
    )
    initial = _chat("Interview coach", prompt, max_tokens=200)
    session_id = f"interview_{current_user.id}_{int(time.time())}"
    return {
        "session_id": session_id,
        "role": session.role,
        "initial_question": initial,
        "duration_minutes": session.duration_minutes,
        "focus_areas": session.focus_areas or ["technical", "behavioral"],
        "ai": True,
    }


@router.post("/{session_id}/message")
async def send_message(
    session_id: str,
    message: str,
    current_user: User = Depends(get_current_user),
):
    """Evaluate answer + ask a follow-up via LLM (JSON)."""
    _ = (session_id, current_user)
    raw = _chat(
        "You are an interview coach. Respond ONLY with valid JSON.",
        (
            "Candidate answer:\n"
            f"{message}\n\n"
            "Return JSON: "
            '{"follow_up_question": str, "feedback": {"clarity": int, "technical_depth": int, "structure": int}, '
            '"is_complete": bool}'
        ),
        max_tokens=500,
    )
    try:
        # Strip markdown fences if model wraps them
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            text = text.rsplit("```", 1)[0]
        data = json.loads(text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM returned non-JSON: {exc}") from exc
    return data


@router.post("/{session_id}/end")
async def end_interview(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """End interview — LLM summary feedback."""
    _ = (session_id, current_user)
    raw = _chat(
        "You are an interview coach. Respond ONLY with valid JSON matching the schema.",
        (
            "Produce final interview feedback JSON with keys: "
            "overall_score (1-10), categories (object of int scores), "
            "strengths (string[]), improvements (string[]), tips (string[])."
        ),
        max_tokens=700,
    )
    try:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            text = text.rsplit("```", 1)[0]
        data = json.loads(text)
        return InterviewFeedback(**data).dict()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM feedback parse failed: {exc}") from exc


@router.get("/questions/{role}")
async def get_practice_questions(
    role: str,
    current_user: User = Depends(get_current_user),
):
    """Generate practice questions for a role via LLM."""
    _ = current_user
    raw = _chat(
        "Respond ONLY with valid JSON.",
        (
            f"Generate interview practice questions for role '{role}'. "
            'JSON shape: {"role": str, "questions": {"technical": [str], "behavioral": [str], "system_design": [str]}}'
        ),
        max_tokens=700,
    )
    try:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            text = text.rsplit("```", 1)[0]
        return json.loads(text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM questions parse failed: {exc}") from exc


@router.post("/evaluate-answer")
async def evaluate_answer(
    question: str,
    answer: str,
    current_user: User = Depends(get_current_user),
):
    """LLM evaluation of a practice answer."""
    _ = current_user
    raw = _chat(
        "Respond ONLY with valid JSON.",
        (
            f"Question: {question}\nAnswer: {answer}\n"
            'Return JSON: {"score": int, "feedback": str, "suggested_improvements": [str]}'
        ),
        max_tokens=400,
    )
    try:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            text = text.rsplit("```", 1)[0]
        return json.loads(text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM evaluation parse failed: {exc}") from exc
