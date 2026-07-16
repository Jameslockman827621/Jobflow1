"""Google OAuth endpoints — real verify path with mocked Google HTTP only in tests."""

from __future__ import annotations

import os
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-32chars")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")
os.environ["GOOGLE_CLIENT_ID"] = "test-google-client-id.apps.googleusercontent.com"
os.environ["GOOGLE_CLIENT_SECRET"] = "test-google-client-secret"

from app.core.config import settings

settings.RATE_LIMIT_PER_MINUTE = 0
settings.GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
settings.GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]

from app.main import app
from app.database import init_db, SessionLocal
from app.models.user import User


@pytest.fixture(scope="module")
def client():
    init_db()
    db = SessionLocal()
    try:
        db.execute(
            __import__("sqlalchemy").text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS google_sub VARCHAR"
            )
        )
        try:
            db.execute(
                __import__("sqlalchemy").text(
                    "ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL"
                )
            )
        except Exception:
            db.rollback()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    return TestClient(app)


def test_google_start_returns_authorize_url(client):
    r = client.get("/api/v1/auth/google")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "accounts.google.com" in data["authorize_url"]
    assert "client_id=test-google-client-id" in data["authorize_url"]
    assert data.get("state")


def test_google_start_503_when_unconfigured(client, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", None)
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", None)
    r = client.get("/api/v1/auth/google")
    assert r.status_code == 503
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", os.environ["GOOGLE_CLIENT_ID"])
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", os.environ["GOOGLE_CLIENT_SECRET"])


def test_google_id_token_login_creates_user(client):
    sub = f"google-sub-{uuid.uuid4().hex[:12]}"
    email = f"g_{uuid.uuid4().hex[:8]}@gmail.com"
    claims = {
        "sub": sub,
        "email": email,
        "email_verified": "true",
        "aud": settings.GOOGLE_CLIENT_ID,
        "given_name": "Grace",
        "family_name": "Hopper",
    }

    with patch(
        "app.services.google_oauth.verify_id_token",
        new=AsyncMock(return_value=claims),
    ):
        r = client.post("/api/v1/auth/google/token", json={"id_token": "fake-id-token"})

    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email
    assert me.json()["is_verified"] is True

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        assert user.google_sub == sub
        assert user.hashed_password is None
    finally:
        db.close()

    bad = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "anything"},
    )
    assert bad.status_code == 401
    assert "Google" in bad.json()["detail"]
