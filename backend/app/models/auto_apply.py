"""
Auto-Apply Job Model

Tracks which jobs the user has approved for the "Approve-and-Go" application queue.
The user approves jobs on the dashboard; the queue page walks them through each one
with the tailored CV attached and the application form pre-filled by the extension.

Status flow: approved → in_progress → applied | skipped
"""

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, DateTime, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base, TimestampMixin


class UserAutoApplyJob(Base, TimestampMixin):
    """
    Jobs the user has approved for the application queue.
    The extension fetches the next 'approved' job, opens the application URL,
    auto-fills the form, attaches the tailored PDF CV, and the user clicks Submit.
    """
    __tablename__ = "user_auto_apply_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)

    # Approval queue status: approved | in_progress | applied | skipped
    status = Column(String, default="approved", index=True)

    # The tailored CV generated when the user approved this job
    tailored_cv_data = Column(JSON)
    ats_score = Column(Float)

    # Tracking
    approved_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)  # When the user started this application
    applied_at = Column(DateTime)  # When the user marked it as submitted
    skipped_at = Column(DateTime)

    # Notes the user can add during the apply flow
    notes = Column(String)

    __table_args__ = (
        UniqueConstraint('user_id', 'job_id', name='uix_user_auto_apply_job'),
    )