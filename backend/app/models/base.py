from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TimestampMixin:
    created_at = Column(DateTime, default=func.utcnow(), nullable=False)
    updated_at = Column(DateTime, default=func.utcnow(), onupdate=func.utcnow(), nullable=False)
