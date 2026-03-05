from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from typing import AsyncGenerator, Generator

from app.core.config import settings
from app.models.base import Base
from app.models import User, Job, Application, UserProfile, Skill

# Sync engine (for migrations, Alembic)
sync_engine = create_engine(settings.DATABASE_URL)

# Async engine (for app)
async_engine = create_async_engine(settings.DATABASE_ASYNC_URL, echo=settings.DEBUG)

# Session factories
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

SessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """Dependency for sync DB sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for async DB sessions"""
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()


def init_db():
    """Create all tables (use Alembic for migrations in production)"""
    Base.metadata.create_all(bind=sync_engine)
