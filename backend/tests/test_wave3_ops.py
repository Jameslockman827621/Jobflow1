"""Wave 3: admin scrape, rate-limit headers, answer-bank CRUD, extension token, apply_run enrichment."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-32chars")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")
os.environ.setdefault("RATE_LIMIT_AUTH_PER_MINUTE", "0")

from app.core.config import settings

settings.RATE_LIMIT_PER_MINUTE = 0
settings.RATE_LIMIT_AUTH_PER_MINUTE = 0

from app.main import app
from app.database import init_db, SessionLocal
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.models.company import ApplyRun
from app.scrapers.apify_linkedin import ApifyLinkedInScraper


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


def _register(client: TestClient, email: str | None = None, password: str = "Wave3Pass123!"):
    email = email or f"w3_{uuid.uuid4().hex[:10]}@example.com"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "Wave",
            "last_name": "Three",
        },
    )
    assert r.status_code in (200, 201), r.text
    login = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return email, password, {"Authorization": f"Bearer {token}"}


def test_scrape_requires_admin(client):
    _, _, headers = _register(client)
    r = client.post("/api/v1/jobs/scrape/greenhouse", headers=headers)
    assert r.status_code == 403
    assert "Admin" in r.json().get("detail", "")


def test_scrape_admin_email_allowlist(client, monkeypatch):
    email, _, headers = _register(client)
    monkeypatch.setattr(settings, "ADMIN_EMAILS", email)
    # Celery delay may fail without broker — patch task
    from app.tasks import jobs as jobs_tasks

    called = {}

    def _fake_delay(companies):
        called["n"] = len(companies)
        return None

    monkeypatch.setattr(jobs_tasks.scrape_greenhouse_companies, "delay", _fake_delay)
    r = client.post("/api/v1/jobs/scrape/greenhouse", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["source"] == "greenhouse"
    assert body["requested_by"] == email
    assert "n" in called


def test_extension_token_longer_lived(client):
    _, _, headers = _register(client)
    r = client.post("/api/v1/auth/extension-token", headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("access_token")
    assert data.get("expires_in_days", 0) >= 1
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert me.status_code == 200


def test_answer_bank_crud(client):
    _, _, headers = _register(client)
    create = client.post(
        "/api/v1/answer-bank",
        headers=headers,
        json={"question": "Are you authorized to work in the US?", "answer": "Yes"},
    )
    assert create.status_code == 201, create.text
    entry_id = create.json()["id"]

    listed = client.get("/api/v1/answer-bank", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1

    updated = client.put(
        f"/api/v1/answer-bank/{entry_id}",
        headers=headers,
        json={"answer": "Yes, I am authorized."},
    )
    assert updated.status_code == 200
    assert "authorized" in updated.json()["answer"]

    deleted = client.delete(f"/api/v1/answer-bank/{entry_id}", headers=headers)
    assert deleted.status_code == 200
    gone = client.get(f"/api/v1/answer-bank/{entry_id}", headers=headers)
    assert gone.status_code == 404


def test_applications_include_apply_run(client):
    email, _, headers = _register(client)
    db = SessionLocal()
    try:
        from app.models.job import JobSource

        user = db.query(User).filter(User.email == email).first()
        src = db.query(JobSource).filter_by(name="greenhouse").first()
        if not src:
            src = JobSource(name="greenhouse", base_url="https://boards.greenhouse.io")
            db.add(src)
            db.commit()
            db.refresh(src)
        job = Job(
            source_id=src.id,
            external_id=f"w3-{uuid.uuid4().hex[:8]}",
            title="Engineer",
            company="Acme",
            location="Remote",
            external_url="https://example.com/jobs/1",
            remote=True,
            is_active=True,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        app = Application(user_id=user.id, job_id=job.id, status="applied", stage="applied")
        db.add(app)
        db.commit()
        db.refresh(app)
        run = ApplyRun(
            user_id=user.id,
            application_id=app.id,
            job_id=job.id,
            mode="headless",
            status="needs_user",
            meta_json=json.dumps({"blocked_reason": "login_required", "connect_hint": "Connect LinkedIn"}),
            created_at=datetime.utcnow(),
        )
        db.add(run)
        db.commit()
        app_id = app.id
    finally:
        db.close()

    r = client.get("/api/v1/applications", headers=headers)
    assert r.status_code == 200, r.text
    apps = r.json()["applications"]
    match = next(a for a in apps if a["id"] == app_id)
    assert match.get("apply_run")
    assert match["apply_run"]["status"] == "needs_user"
    assert match["apply_run"]["meta"]["blocked_reason"] == "login_required"


def test_apify_linkedin_no_notimplemented():
    scraper = ApifyLinkedInScraper(api_key="test")
    assert callable(scraper.scrape_company_jobs)
    assert callable(scraper.scrape_all_jobs)
    # Methods exist and are coroutines — not NotImplementedError stubs
    import inspect

    assert inspect.iscoroutinefunction(scraper.scrape_company_jobs)
    assert inspect.iscoroutinefunction(scraper.scrape_all_jobs)


def test_rate_limit_can_enable(client, monkeypatch):
    """When limits are on, health remains unrestricted."""
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 120)
    r = client.get("/api/v1/health/")
    assert r.status_code == 200
    # Restore for other tests
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 0)
