"""Lookup / upsert saved answers for recurring ATS questions."""

from __future__ import annotations

import hashlib
import re
from typing import Optional

from sqlalchemy.orm import Session

from app.models.answer_bank import AnswerBankEntry


def normalize_question(question: str) -> str:
    q = re.sub(r"\s+", " ", (question or "").strip().lower())
    q = re.sub(r"[*：:]+$", "", q).strip()
    return q[:500]


def question_hash(question: str) -> str:
    return hashlib.sha256(normalize_question(question).encode("utf-8")).hexdigest()


def lookup_answer(db: Session, user_id: int, question: str) -> Optional[str]:
    if not question or not user_id:
        return None
    row = (
        db.query(AnswerBankEntry)
        .filter(
            AnswerBankEntry.user_id == user_id,
            AnswerBankEntry.question_hash == question_hash(question),
        )
        .first()
    )
    if not row:
        return None
    row.use_count = (row.use_count or 0) + 1
    try:
        db.commit()
    except Exception:
        db.rollback()
    return row.answer


def upsert_answer(db: Session, user_id: int, question: str, answer: str) -> AnswerBankEntry:
    qh = question_hash(question)
    row = (
        db.query(AnswerBankEntry)
        .filter(AnswerBankEntry.user_id == user_id, AnswerBankEntry.question_hash == qh)
        .first()
    )
    if row:
        row.answer = answer
        row.question = (question or "")[:2000]
        row.use_count = (row.use_count or 0) + 1
    else:
        row = AnswerBankEntry(
            user_id=user_id,
            question_hash=qh,
            question=(question or "")[:2000],
            answer=answer,
            use_count=1,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row
