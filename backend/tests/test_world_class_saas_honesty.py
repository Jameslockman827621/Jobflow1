"""Honesty / no-mock world-class SaaS guards."""

from __future__ import annotations

import os
import uuid

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-32chars")

from app.main import app
from app.database import init_db, SessionLocal
from app.models.user import User
from app.models.job import Job, JobSource
from app.models.application import Application
from app.services.apply_limits import check_apply_quota, PLAN_QUOTAS
from app.services.ai_cv import AICVService, AINotConfiguredError
from app.services.session_crypto import encrypt_storage_state, decrypt_storage_state_dict


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


def _auth(client, plan="free"):
    email = f"wc_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "WorldClass123!",
            "first_name": "World",
            "last_name": "Class",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "WorldClass123!"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        user.subscription_plan = plan
        db.commit()
    finally:
        db.close()
    return headers, email


def test_free_plan_quota_is_five():
    assert PLAN_QUOTAS["free"]["monthly"] == 5
    assert PLAN_QUOTAS["free"]["daily"] == 5


def test_ai_cv_fails_without_key(monkeypatch):
    monkeypatch.setattr("app.services.ai_cv.settings.OPENAI_API_KEY", None)
    svc = AICVService()
    svc.client = None
    with pytest.raises(AINotConfiguredError):
        svc.tailor_cv("resume", "job", {})


def test_session_encryption_roundtrip():
    state = {"cookies": [{"name": "li_at", "value": "secret"}], "origins": []}
    enc = encrypt_storage_state(state)
    assert enc.startswith("enc:v1:")
    assert "li_at" not in enc or "secret" not in enc
    back = decrypt_storage_state_dict(enc)
    assert back["cookies"][0]["value"] == "secret"


def test_submit_requires_manual_flag(client):
    headers, email = _auth(client)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        src = db.query(JobSource).filter_by(name="greenhouse").first()
        if not src:
            src = JobSource(name="greenhouse", base_url="https://boards.greenhouse.io")
            db.add(src)
            db.commit()
            db.refresh(src)
        job = Job(
            source_id=src.id,
            external_id=f"wc-{uuid.uuid4().hex[:8]}",
            external_url="https://boards.greenhouse.io/acme/jobs/1",
            title="Honesty Role",
            company="Acme",
            is_active=True,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        app_row = Application(user_id=user.id, job_id=job.id, status="in_progress")
        db.add(app_row)
        db.commit()
        db.refresh(app_row)
        app_id = app_row.id
    finally:
        db.close()

    bad = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    assert bad.status_code == 400
    assert bad.json()["detail"]["error"] == "genuine_submit_required"

    ok = client.post(f"/api/v1/applications/{app_id}/submit?manual=true", headers=headers)
    assert ok.status_code == 200
    assert ok.json()["manual"] is True


def test_users_placeholder_gone(client):
    r = client.post("/api/v1/users/register", json={"email": "a@b.com", "password": "x"})
    assert r.status_code == 410


def test_interview_coach_503_without_openai(client, monkeypatch):
    monkeypatch.setattr("app.api.interview_coach.settings.OPENAI_API_KEY", None)
    headers, _ = _auth(client)
    r = client.post(
        "/api/v1/interview-coach/start",
        headers=headers,
        json={"role": "software engineer"},
    )
    assert r.status_code == 503


def test_quota_endpoint_includes_plan(client):
    headers, _ = _auth(client, plan="pro")
    r = client.get("/api/v1/apply-engine/quota", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["plan"] == "pro"
    assert body["monthly_limit"] == PLAN_QUOTAS["pro"]["monthly"]
    assert "remaining_month" in body


def test_scrape_requires_auth(client):
    r = client.post("/api/v1/jobs/scrape/greenhouse")
    assert r.status_code in (401, 403)
