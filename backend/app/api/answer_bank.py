"""Answer bank CRUD — saved ATS question answers for reuse."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.answer_bank import AnswerBankEntry
from app.models.user import User
from app.services.answer_bank import question_hash, upsert_answer

router = APIRouter()


class AnswerCreate(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    answer: str = Field(..., min_length=1, max_length=10000)


class AnswerUpdate(BaseModel):
    question: Optional[str] = Field(None, min_length=1, max_length=2000)
    answer: Optional[str] = Field(None, min_length=1, max_length=10000)


def _serialize(row: AnswerBankEntry) -> dict:
    return {
        "id": row.id,
        "question": row.question,
        "answer": row.answer,
        "use_count": row.use_count or 0,
        "updated_at": row.updated_at.isoformat() if getattr(row, "updated_at", None) else None,
    }


@router.get("")
async def list_answers(
    q: Optional[str] = Query(None, description="Filter by question substring"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(AnswerBankEntry).filter(AnswerBankEntry.user_id == current_user.id)
    if q:
        query = query.filter(AnswerBankEntry.question.ilike(f"%{q.strip()}%"))
    total = query.count()
    rows = (
        query.order_by(AnswerBankEntry.updated_at.desc().nullslast(), AnswerBankEntry.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {"answers": [_serialize(r) for r in rows], "total": total}


@router.get("/{entry_id}")
async def get_answer(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(AnswerBankEntry)
        .filter(AnswerBankEntry.id == entry_id, AnswerBankEntry.user_id == current_user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Answer not found")
    return _serialize(row)


@router.post("", status_code=201)
async def create_answer(
    body: AnswerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = upsert_answer(db, current_user.id, body.question, body.answer)
    return _serialize(row)


@router.put("/{entry_id}")
async def update_answer(
    entry_id: int,
    body: AnswerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(AnswerBankEntry)
        .filter(AnswerBankEntry.id == entry_id, AnswerBankEntry.user_id == current_user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Answer not found")
    if body.question is not None:
        row.question = body.question[:2000]
        row.question_hash = question_hash(body.question)
    if body.answer is not None:
        row.answer = body.answer
    db.commit()
    db.refresh(row)
    return _serialize(row)


@router.delete("/{entry_id}")
async def delete_answer(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(AnswerBankEntry)
        .filter(AnswerBankEntry.id == entry_id, AnswerBankEntry.user_id == current_user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Answer not found")
    db.delete(row)
    db.commit()
    return {"ok": True, "id": entry_id}
