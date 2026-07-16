"""Wave 5: monitor auto-queue, fingerprint concurrency, log redaction."""

from __future__ import annotations

import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-32chars")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")

from app.core.config import settings

settings.RATE_LIMIT_PER_MINUTE = 0

from app.main import app
from app.database import init_db, SessionLocal
from app.models.user import User
from app.models.job import Job, JobSource
from app.models.profile import UserProfile
from app.models.preferences import UserPreferences
from app.models.auto_apply import UserAutoApplyJob
from app.services.monitor_auto_queue import auto_queue_new_jobs_for_opted_in_users
from app.services.proxy_pool import fingerprint_headers
from app.core.log_redact import redact_text


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


def _register(client: TestClient):
    email = f"w5_{uuid.uuid4().hex[:10]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Wave5Pass123!",
            "first_name": "Wave",
            "last_name": "Five",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "Wave5Pass123!"},
    ).json()["access_token"]
    return email, {"Authorization": f"Bearer {token}"}


def test_fingerprint_sticky_under_concurrency():
    def once(_):
        return fingerprint_headers(user_id=777)["User-Agent"]

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(once, range(40)))
    assert len(set(results)) == 1
    other = fingerprint_headers(user_id=778)["User-Agent"]
    assert other != results[0] or fingerprint_headers(user_id=778)["Sec-Ch-Ua-Platform"] != fingerprint_headers(user_id=777)["Sec-Ch-Ua-Platform"]


def test_log_redaction_masks_cookies():
    raw = 'synced cookie li_at=AQEDAR8_secretvalue123 Authorization: Bearer abcdefghijklmnop'
    out = redact_text(raw)
    assert "AQEDAR8_secretvalue123" not in out
    assert "abcdefghijklmnop" not in out
    assert "REDACTED" in out


def test_monitor_auto_queue_settings_and_queue(client):
    email, headers = _register(client)
    # Opt in
    patch = client.patch(
        "/api/v1/apply-engine/settings",
        headers=headers,
        json={"monitor_auto_queue": True},
    )
    assert patch.status_code == 200, patch.text
    assert patch.json()["monitor_auto_queue"] is True

    settings_get = client.get("/api/v1/apply-engine/settings", headers=headers)
    assert settings_get.json()["monitor_auto_queue"] is True

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        user.monitor_auto_queue = True
        prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
        if not prefs:
            prefs = UserPreferences(user_id=user.id, target_companies=["Acme"], is_active=True)
            db.add(prefs)
        else:
            prefs.target_companies = ["Acme"]
            prefs.is_active = True
        src = db.query(JobSource).filter_by(name="greenhouse").first()
        if not src:
            src = JobSource(name="greenhouse", base_url="https://boards.greenhouse.io")
            db.add(src)
            db.commit()
            db.refresh(src)
        job = Job(
            source_id=src.id,
            external_id=f"mq-{uuid.uuid4().hex[:8]}",
            external_url=f"https://example.com/j/{uuid.uuid4().hex[:6]}",
            title="Software Engineer",
            company="Acme Corp",
            location="Remote",
            remote=True,
            is_active=True,
            skills_required=["python"],
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id
        uid = user.id
        result = auto_queue_new_jobs_for_opted_in_users(
            db, company_name="Acme Corp", job_ids=[job_id], min_score=0.0
        )
        assert result["queued"] >= 1
        row = (
            db.query(UserAutoApplyJob)
            .filter(UserAutoApplyJob.user_id == uid, UserAutoApplyJob.job_id == job_id)
            .first()
        )
        assert row is not None
    finally:
        db.close()
