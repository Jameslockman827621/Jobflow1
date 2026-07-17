"""Persisted browser storage_state for LinkedIn / Indeed logged-in apply."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Index, UniqueConstraint

from app.models.base import Base, TimestampMixin


class BoardSession(Base, TimestampMixin):
    __tablename__ = "board_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    board = Column(String(40), nullable=False)  # linkedin | indeed
    # Playwright storage_state JSON (cookies + origins localStorage)
    storage_state_json = Column(Text, nullable=False)
    label = Column(String(120), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    is_valid = Column(Integer, default=1)  # 1/0 for SQLite friendliness

    __table_args__ = (
        UniqueConstraint("user_id", "board", name="uix_board_session_user_board"),
        Index("idx_board_session_user", "user_id"),
    )
