"""Verify empty database can be bootstrapped with alembic upgrade head alone."""

from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import create_engine, text, inspect

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-32chars")

from app.core.config import settings


REQUIRED_TABLES = {
    "users",
    "jobs",
    "job_sources",
    "applications",
    "cvs",
    "user_profiles",
    "monitored_companies",
    "apply_runs",
    "board_sessions",
    "answer_bank",
}


def _admin_url() -> str:
    # postgresql://user:pass@host:port/dbname → .../postgres
    url = settings.DATABASE_URL
    if "/" not in url.rsplit("@", 1)[-1]:
        pytest.skip("Cannot derive admin DB URL")
    base, _dbname = url.rsplit("/", 1)
    return f"{base}/postgres"


@pytest.fixture
def fresh_db_url():
    db_name = f"jobscale_alembic_{uuid.uuid4().hex[:8]}"
    admin = create_engine(_admin_url(), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    url = settings.DATABASE_URL.rsplit("/", 1)[0] + f"/{db_name}"
    yield url
    with admin.connect() as conn:
        # Terminate sessions then drop
        conn.execute(
            text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = :n AND pid <> pg_backend_pid()"
            ),
            {"n": db_name},
        )
        conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
    admin.dispose()


def test_alembic_upgrade_creates_core_tables(fresh_db_url, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", fresh_db_url)
    monkeypatch.setattr(settings, "DATABASE_URL", fresh_db_url)

    from alembic.config import Config
    from alembic import command

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cfg = Config(os.path.join(root, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", fresh_db_url)
    command.upgrade(cfg, "head")

    eng = create_engine(fresh_db_url)
    try:
        tables = set(inspect(eng).get_table_names())
        missing = REQUIRED_TABLES - tables
        assert not missing, f"Missing tables after alembic upgrade: {missing}"
        # Additive columns from later revisions
        cols = {c["name"] for c in inspect(eng).get_columns("users")}
        assert "google_sub" in cols
        assert "is_admin" in cols
        assert "monitor_auto_queue" in cols
    finally:
        eng.dispose()
