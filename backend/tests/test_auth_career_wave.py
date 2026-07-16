"""Auth password reset / verify + career goals honesty tests."""

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
from app.models.profile import UserProfile
from app.api.auth import _purpose_token


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


def test_forgot_and_reset_password(client):
    email = f"reset_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "OldPass123!",
            "first_name": "Reset",
            "last_name": "User",
        },
    )
    # Always 200
    r = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert r.status_code == 200
    token = _purpose_token(email, "reset_password", minutes=30)
    bad = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "not-a-token", "password": "NewPass123!"},
    )
    assert bad.status_code == 400
    ok = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "password": "NewPass123!"},
    )
    assert ok.status_code == 200
    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "NewPass123!"},
    )
    assert login.status_code == 200


def test_verify_email_flow(client):
    email = f"verify_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "VerifyPass123!",
            "first_name": "Ver",
            "last_name": "User",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "VerifyPass123!"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/api/v1/auth/me", headers=headers).json()
    assert me.get("is_verified") is False
    vtoken = _purpose_token(email, "verify_email", minutes=60)
    # Purpose token cannot be used as session
    spoof = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {vtoken}"})
    assert spoof.status_code == 401
    done = client.post("/api/v1/auth/verify-email", json={"token": vtoken})
    assert done.status_code == 200
    me2 = client.get("/api/v1/auth/me", headers=headers).json()
    assert me2.get("is_verified") is True


def test_career_goals_persist(client):
    email = f"career_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "CareerPass123!",
            "first_name": "Car",
            "last_name": "Eer",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "CareerPass123!"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        profile.current_title = "Software Engineer"
        profile.years_of_experience = 3
        db.commit()
    finally:
        db.close()

    analysis = client.get("/api/v1/career/analysis", headers=headers)
    assert analysis.status_code == 200
    body = analysis.json()
    assert "current_level" in body
    assert "skill_gaps" in body

    saved = client.post(
        "/api/v1/career/goals",
        headers=headers,
        json={"target_roles": ["Staff Engineer"], "target_salary": 200000},
    )
    assert saved.status_code == 200
    goals = client.get("/api/v1/career/goals", headers=headers).json()
    assert "Staff Engineer" in (goals["goals"]["target_roles"] or [])
    assert goals["goals"]["target_salary"] == 200000


def test_health_ready_includes_ops(client):
    r = client.get("/api/v1/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert "celery_workers" in body["checks"]
    assert "ops_hint" in body
    assert "auto_seed_demo_jobs" in body


def test_production_disables_demo_seed():
    from app.core.config import Settings

    s = Settings(ENVIRONMENT="production", SECRET_KEY="x" * 40, AUTO_SEED_DEMO_JOBS=True)
    assert s.AUTO_SEED_DEMO_JOBS is False
