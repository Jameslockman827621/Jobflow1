"""
Auto-Apply Job Model

Tracks which jobs the user has selected for auto-apply via the Chrome extension.
When the user visits a matching job page, the extension auto-applies.
"""

from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class UserAutoApplyJob(Base, TimestampMixin):
    """
    Jobs the user has selected for auto-apply in the dashboard.
    The extension fetches this list and auto-applies when the user visits a matching job page.
    """
    __tablename__ = "user_auto_apply_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'job_id', name='uix_user_auto_apply_job'),
    )
