"""Scale / quota tests for hundreds of applications per user path."""

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
from app.models.cv import CV
from app.models.company import ApplyRun
from app.services.apply_limits import check_apply_quota, DEFAULT_DAILY_LIMIT, DEFAULT_HOURLY_LIMIT


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


@pytest.fixture(scope="module")
def auth(client):
    email = f"scale_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "ScalePass123!", "first_name": "Scale", "last_name": "Tester"},
    )
    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "ScalePass123!"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email


def test_quota_endpoint(client, auth):
    headers, _ = auth
    r = client.get("/api/v1/apply-engine/quota", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["daily_limit"] == DEFAULT_DAILY_LIMIT
    assert body["hourly_limit"] == DEFAULT_HOURLY_LIMIT
    assert body["allowed"] is True


def test_batch_create_many_applications(client, auth):
    """Simulate selecting hundreds of jobs and packaging applies (no live submit)."""
    headers, email = auth
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        source = db.query(JobSource).filter_by(name="greenhouse").first()
        if not source:
            source = JobSource(name="greenhouse", base_url="https://boards-api.greenhouse.io")
            db.add(source)
            db.commit()
            db.refresh(source)
        if not db.query(CV).filter(CV.user_id == user.id).first():
            db.add(
                CV(
                    user_id=user.id,
                    full_name="Scale Tester",
                    email=email,
                    phone="+15555550111",
                    linkedin_url="https://linkedin.com/in/scale",
                    skills=["Python"],
                    is_primary=True,
                )
            )
            db.commit()

        job_ids = []
        for i in range(120):
            job = Job(
                source_id=source.id,
                external_id=f"scale-{uuid.uuid4().hex[:10]}",
                external_url=f"https://boards.greenhouse.io/example/jobs/{1000+i}",
                title=f"Engineer {i}",
                company="ExampleCo",
                location="Remote",
                is_active=True,
            )
            db.add(job)
            db.flush()
            job_ids.append(job.id)
        db.commit()
    finally:
        db.close()

    # Batch-start in chunks of 50
    created = 0
    for i in range(0, len(job_ids), 50):
        chunk = job_ids[i : i + 50]
        r = client.post("/api/v1/applications/batch-start", headers=headers, json={"job_ids": chunk})
        assert r.status_code == 200, r.text
        created += r.json()["total"]
    assert created >= 100

    ready = client.get("/api/v1/applications/ready-to-apply", headers=headers)
    assert ready.status_code == 200
    assert ready.json()["total"] >= 100


def test_quota_blocks_over_hourly(client, auth):
    headers, email = auth
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        # Simulate many prior runs this hour
        for _ in range(DEFAULT_HOURLY_LIMIT):
            db.add(ApplyRun(user_id=user.id, mode="headless", status="filled", ats_type="greenhouse"))
        db.commit()
        quota = check_apply_quota(db, user.id, requested=1)
        assert quota["allowed"] is False
        assert "hourly" in (quota["reason"] or "")
    finally:
        db.close()
