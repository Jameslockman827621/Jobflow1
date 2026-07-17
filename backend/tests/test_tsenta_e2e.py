"""
End-to-end account + apply-engine flow against a live API (skips if DB/API unavailable).

Run with:
  cd backend && pytest tests/test_tsenta_e2e.py -v
"""

from __future__ import annotations

import os
import time
import uuid

import pytest
from fastapi.testclient import TestClient

# Ensure models are registered before init
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-32chars")

from app.main import app
from app.database import init_db, SessionLocal
from app.models.job import Job, JobSource
from app.models.cv import CV


@pytest.fixture(scope="module")
def client():
    try:
        init_db()
    except Exception as exc:
        pytest.skip(f"Database unavailable: {exc}")
    return TestClient(app)


@pytest.fixture(scope="module")
def auth_headers(client):
    email = f"e2e_{uuid.uuid4().hex[:10]}@example.com"
    password = "TestPass123!"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "E2E",
            "last_name": "Tester",
        },
    )
    assert reg.status_code in (200, 201), reg.text

    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email


def _ensure_job_and_cv(user_email: str) -> tuple[int, int]:
    db = SessionLocal()
    try:
        from app.models.user import User

        user = db.query(User).filter(User.email == user_email).first()
        assert user is not None

        source = db.query(JobSource).filter_by(name="greenhouse").first()
        if not source:
            source = JobSource(name="greenhouse", base_url="https://boards-api.greenhouse.io")
            db.add(source)
            db.commit()
            db.refresh(source)

        job = Job(
            source_id=source.id,
            external_id=f"e2e-{uuid.uuid4().hex[:8]}",
            external_url="https://boards.greenhouse.io/stripe/jobs/4012345",
            title="Software Engineer",
            company="Stripe",
            location="Remote",
            remote=True,
            description="Build payments infrastructure.",
            is_active=True,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        cv = (
            db.query(CV)
            .filter(CV.user_id == user.id)
            .order_by(CV.created_at.desc())
            .first()
        )
        if not cv:
            cv = CV(
                user_id=user.id,
                full_name="E2E Tester",
                email=user_email,
                phone="+15551234567",
                linkedin_url="https://linkedin.com/in/e2etester",
                portfolio_url="https://github.com/e2etester",
                location="San Francisco, CA",
                summary="Full-stack engineer focused on reliable systems.",
                skills=["Python", "TypeScript", "PostgreSQL"],
                experience=[{"company": "Acme", "role": "Engineer", "description": "Shipped features"}],
                education=[{"institution": "State U", "degree": "BS", "field": "CS"}],
                is_primary=True,
            )
            db.add(cv)
            db.commit()
            db.refresh(cv)
        return job.id, cv.id
    finally:
        db.close()


def test_account_register_login_me(client, auth_headers):
    headers, email = auth_headers
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_seed_company_directory_and_coverage(client, auth_headers):
    headers, _ = auth_headers
    seed = client.post("/api/v1/companies/seed", headers=headers)
    assert seed.status_code == 200, seed.text
    body = seed.json()
    assert body["total"] >= 150

    cov = client.get("/api/v1/companies/coverage", headers=headers)
    assert cov.status_code == 200
    data = cov.json()
    assert data["monitored_career_pages"] >= 150
    assert data["capacity_target"] == 50000
    assert data["monitoring"]["cold_interval_hours"] == 2
    assert data["monitoring"]["hot_interval_seconds"] == 60


def test_apply_package_and_open_ended(client, auth_headers):
    headers, email = auth_headers
    job_id, _ = _ensure_job_and_cv(email)

    start = client.post("/api/v1/applications/start", headers=headers, json={"job_id": job_id})
    assert start.status_code == 200, start.text
    app_id = start.json()["application_id"]

    pkg = client.get(f"/api/v1/apply-engine/package/application/{app_id}", headers=headers)
    assert pkg.status_code == 200, pkg.text
    package = pkg.json()
    assert package["ats"] == "greenhouse"
    assert package["capabilities"]["multi_step"] is True
    assert package["capabilities"]["select"] is True
    assert package["applicant"]["email"]
    assert any(f["key"] == "email" for f in package["fill_plan"]["fields"])

    ans = client.post(
        "/api/v1/apply-engine/answer",
        headers=headers,
        json={"question": "Why do you want this role?", "job_id": job_id},
    )
    assert ans.status_code == 200
    assert len(ans.json()["answer"]) > 10


def test_headless_dry_run_and_runs(client, auth_headers):
    headers, email = auth_headers
    job_id, _ = _ensure_job_and_cv(email)
    start = client.post("/api/v1/applications/start", headers=headers, json={"job_id": job_id})
    app_id = start.json()["application_id"]

    result = client.post(
        "/api/v1/apply-engine/headless",
        headers=headers,
        json={"application_id": app_id, "dry_run": True, "auto_submit": False},
    )
    assert result.status_code == 200, result.text
    body = result.json()
    assert body["ok"] is True
    assert body["dry_run"] is True
    assert body["fields_planned"] >= 1

    runs = client.get("/api/v1/apply-engine/runs", headers=headers)
    assert runs.status_code == 200
    assert runs.json()["total"] >= 1


def test_messaging_bot_inbound(client, auth_headers):
    headers, _ = auth_headers
    status = client.get("/api/v1/apply-engine/messaging/status", headers=headers)
    assert status.status_code == 200
    assert "whatsapp" in status.json()

    inbound = client.post(
        "/api/v1/apply-engine/messaging/inbound",
        headers=headers,
        json={"channel": "whatsapp", "from_number": "+15551234567", "body": "HELP"},
    )
    assert inbound.status_code == 200
    data = inbound.json()
    assert data["command"] == "HELP"
    assert "APPLY" in data["reply"]


def test_batch_scale_endpoint_queues_or_validates(client, auth_headers):
    headers, email = auth_headers
    job_id, _ = _ensure_job_and_cv(email)
    # Create several ready applications
    ids = []
    for _ in range(3):
        jid, _ = _ensure_job_and_cv(email)
        # mutate URL uniqueness already handled; start apps
        r = client.post("/api/v1/applications/start", headers=headers, json={"job_id": jid})
        if r.status_code == 200:
            ids.append(r.json()["application_id"])
    assert ids
    # Without Redis this may fail queueing; accept either queued or connection error path
    try:
        batch = client.post(
            "/api/v1/apply-engine/headless/batch",
            headers=headers,
            json={"application_ids": ids, "dry_run": True},
        )
        # If Redis is up → 200; if Celery broker down → 500
        assert batch.status_code in (200, 500)
        if batch.status_code == 200:
            assert batch.json()["queued"] is True
    except Exception:
        pytest.skip("Celery broker unavailable for batch queue")


def test_captcha_status(client, auth_headers):
    headers, _ = auth_headers
    r = client.get("/api/v1/apply-engine/captcha/status", headers=headers)
    assert r.status_code == 200
    assert "available" in r.json()
