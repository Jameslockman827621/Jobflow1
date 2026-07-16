from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from typing import AsyncGenerator, Generator

from app.core.config import settings
from app.models.base import Base
from app.models import User, Job, Application, UserProfile, Skill, MonitoredCompany, ApplyRun  # noqa: F401

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
    """Create / migrate schema.

    Empty databases prefer Alembic (`upgrade head`) so production bootstrap
    matches CI. Databases that already have tables use create_all(checkfirst)
    plus additive ALTERs for speed (tests) and safety.
    """
    from sqlalchemy import inspect as sa_inspect

    try:
        existing = set(sa_inspect(sync_engine).get_table_names())
    except Exception:
        existing = set()

    if not existing:
        try:
            import os
            from alembic.config import Config
            from alembic import command

            root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            cfg = Config(os.path.join(root, "alembic.ini"))
            cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
            command.upgrade(cfg, "head")
            return
        except Exception:
            pass

    Base.metadata.create_all(bind=sync_engine)
    # Additive columns that create_all will not alter onto existing tables
    stmts = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS auto_apply_submit BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS monitor_auto_queue BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS google_sub VARCHAR",
    ]
    try:
        with sync_engine.begin() as conn:
            for sql in stmts:
                try:
                    conn.exec_driver_sql(sql)
                except Exception:
                    # SQLite older / non-Postgres dialects may not support IF NOT EXISTS
                    pass
    except Exception:
        pass
