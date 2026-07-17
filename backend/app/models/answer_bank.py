"""Persisted Q→A bank so custom application questions improve at scale."""

from sqlalchemy import Column, Integer, String, Text, Index, UniqueConstraint

from app.models.base import Base, TimestampMixin


class AnswerBankEntry(Base, TimestampMixin):
    __tablename__ = "answer_bank"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    question_hash = Column(String(64), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    use_count = Column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint("user_id", "question_hash", name="uix_answer_bank_user_q"),
        Index("idx_answer_bank_user", "user_id"),
    )
