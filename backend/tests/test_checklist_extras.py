"""Coverage for webhook ingest, captcha mock, resume files, health ready, report."""

from __future__ import annotations

import os
import uuid

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-32chars")
os.environ["CAPTCHA_MOCK"] = "true"
os.environ["TWOCAPTCHA_API_KEY"] = "mock"

from app.core.config import settings

# Force mock for this module
settings.CAPTCHA_MOCK = True
settings.TWOCAPTCHA_API_KEY = "mock"

from app.main import app
from app.database import init_db, SessionLocal
from app.models.user import User
from app.models.job import Job, JobSource
from app.models.cv import CV
from app.services.captcha import CaptchaService
from app.services.resume_files import ensure_resume_local_path


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


@pytest.fixture(scope="module")
def auth(client):
    email = f"chk_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "CheckPass123!", "first_name": "Check", "last_name": "List"},
    )
    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "CheckPass123!"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email


@pytest.mark.asyncio
async def test_captcha_mock_token():
    svc = CaptchaService(api_key="mock")
    result = await svc.solve_recaptcha_v2("site", "https://example.com")
    assert result["ok"] is True
    assert result["token"] == "mock-captcha-token"


def test_resume_file_materialize():
    applicant = {
        "full_name": "Check List",
        "email": "chk@example.com",
        "phone": "+15555550100",
        "summary": "Hello",
        "skills": ["Python"],
    }
    path = ensure_resume_local_path(999, applicant, None)
    assert path
    assert os.path.exists(path)
    assert os.path.getsize(path) > 10


def test_health_ready(client):
    r = client.get("/api/v1/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert "ready" in body
    assert "checks" in body
    assert "captcha_available" in body["checks"]
    assert "headless_apply_enabled" in body["checks"]


def test_webhook_job_ingest(client):
    settings.WEBHOOK_SECRET = "test-secret"
    payload = {
        "ats_type": "greenhouse",
        "company_slug": "webhookco",
        "jobs": [
            {
                "title": "Webhook Engineer",
                "external_id": f"wh-{uuid.uuid4().hex[:8]}",
                "external_url": f"https://boards.greenhouse.io/webhookco/jobs/{uuid.uuid4().hex[:6]}",
                "location": "Remote",
                "description": "From webhook",
            }
        ],
    }
    r = client.post(
        "/api/v1/webhooks/jobs",
        json=payload,
        headers={"X-JobScale-Webhook-Secret": "test-secret"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert (body.get("created") or 0) + (body.get("updated") or 0) + (body.get("saved") or 0) >= 1 or body.get("ok") is True


def test_extension_report(client, auth):
    headers, email = auth
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        src = db.query(JobSource).filter_by(name="greenhouse").first()
        if not src:
            src = JobSource(name="greenhouse", base_url="https://boards-api.greenhouse.io")
            db.add(src)
            db.commit()
            db.refresh(src)
        job = Job(
            source_id=src.id,
            external_id=f"rep-{uuid.uuid4().hex[:8]}",
            external_url="https://boards.greenhouse.io/x/jobs/1",
            title="Report Role",
            company="ReportCo",
            is_active=True,
        )
        db.add(job)
        if not db.query(CV).filter(CV.user_id == user.id).first():
            db.add(CV(user_id=user.id, full_name="Check List", email=email, is_primary=True))
        db.commit()
        db.refresh(job)
        job_id = job.id
    finally:
        db.close()

    start = client.post("/api/v1/applications/start", headers=headers, json={"job_id": job_id})
    app_id = start.json()["application_id"]
    r = client.post(
        "/api/v1/apply-engine/report",
        headers=headers,
        json={
            "application_id": app_id,
            "fields_filled": 5,
            "steps_completed": 2,
            "status": "needs_user",
            "ats": "greenhouse",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("ok") is True or body.get("id") or body.get("apply_run_id")


def test_seed_catalog_size(client, auth):
    headers, _ = auth
    r = client.post("/api/v1/companies/seed", headers=headers)
    assert r.status_code == 200
    assert r.json()["total"] >= 500
