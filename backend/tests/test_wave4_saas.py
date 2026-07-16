"""Wave 4: real referral rewards, unsubscribe, ops metrics, production email honesty."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta

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
from app.models.referral import ReferralCode
from app.services.unsubscribe import make_unsubscribe_token, parse_unsubscribe_token
from app.services.email import EmailService
from app.services.referral_rewards import grant_referee_pro_trial


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


def _register(client: TestClient, email: str | None = None, password: str = "Wave4Pass123!"):
    email = email or f"w4_{uuid.uuid4().hex[:10]}@example.com"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "Wave",
            "last_name": "Four",
        },
    )
    assert r.status_code in (200, 201), r.text
    login = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return email, {"Authorization": f"Bearer {token}"}


def test_referral_claim_grants_pro_trial(client):
    referrer_email, referrer_headers = _register(client)
    code_res = client.get("/api/v1/referrals/code", headers=referrer_headers)
    assert code_res.status_code == 200, code_res.text
    code = code_res.json()["code"]
    assert "/login?mode=signup&ref=" in code_res.json()["link"]
    assert "localhost:3000/signup" not in code_res.json()["link"]

    friend_email, friend_headers = _register(client)
    claim = client.post(
        "/api/v1/referrals/claim",
        headers=friend_headers,
        json={"code": code},
    )
    assert claim.status_code == 200, claim.text
    body = claim.json()
    assert body["status"] == "claimed"
    assert body["trial"]["granted"] is True
    assert body["trial"]["plan"] == "pro"
    # Referrer credit may be pending without Stripe customer — honest
    assert "referrer_bonus" in body
    assert body["referrer_bonus"]["pending"] in (True, False)

    db = SessionLocal()
    try:
        friend = db.query(User).filter(User.email == friend_email).first()
        assert friend.subscription_plan == "pro"
        assert friend.subscription_end is not None
        assert friend.subscription_end > datetime.utcnow()
        # Self-referral blocked
        self_claim = client.post(
            "/api/v1/referrals/claim",
            headers=referrer_headers,
            json={"code": code},
        )
        assert self_claim.status_code == 400
    finally:
        db.close()


def test_unsubscribe_token_disables_alerts(client):
    email, headers = _register(client)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        user.email_alerts_enabled = True
        user.alert_frequency = "daily"
        db.commit()
        uid = user.id
    finally:
        db.close()

    token = make_unsubscribe_token(uid)
    assert parse_unsubscribe_token(token) == uid
    r = client.get(f"/api/v1/alerts/unsubscribe?token={token}")
    assert r.status_code == 200, r.text
    assert r.json()["email_alerts_enabled"] is False

    prefs = client.get("/api/v1/alerts/preferences", headers=headers)
    assert prefs.status_code == 200
    assert prefs.json()["email_alerts_enabled"] is False
    assert prefs.json()["alert_frequency"] == "off"


def test_alert_preferences_return_fresh_frequency(client):
    _, headers = _register(client)
    r = client.put(
        "/api/v1/alerts/preferences",
        headers=headers,
        json={"alert_frequency": "weekly", "email_alerts_enabled": True},
    )
    assert r.status_code == 200
    assert r.json()["alert_frequency"] == "weekly"


def test_production_email_no_console_success(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "DEBUG", True)
    monkeypatch.setattr(settings, "SENDGRID_API_KEY", None)
    svc = EmailService()
    svc.smtp_user = ""
    svc.smtp_password = ""
    ok = svc.send_email("a@b.com", "t", "<p>hi</p>")
    assert ok is False
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")


def test_assert_safe_for_production_cors(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "SECRET_KEY", "a" * 40)
    monkeypatch.setattr(settings, "CORS_ORIGINS", ["*"])
    with pytest.raises(RuntimeError, match="CORS"):
        settings.assert_safe_for_production()
    monkeypatch.setattr(settings, "CORS_ORIGINS", ["https://app.jobscale.app"])
    settings.assert_safe_for_production()
    assert settings.DEBUG is False
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "DEBUG", True)


def test_ops_metrics_admin_only(client, monkeypatch):
    email, headers = _register(client)
    denied = client.get("/api/v1/apply-engine/metrics/ops", headers=headers)
    assert denied.status_code == 403
    monkeypatch.setattr(settings, "ADMIN_EMAILS", email)
    ok = client.get("/api/v1/apply-engine/metrics/ops", headers=headers)
    assert ok.status_code == 200, ok.text
    assert "stale" in ok.json()


def test_grant_referee_does_not_downgrade_premium():
    u = User(email="x@y.com", hashed_password="x", subscription_plan="premium", subscription_status="active")
    u.subscription_end = datetime.utcnow() + timedelta(days=90)
    result = grant_referee_pro_trial(u)
    assert result["granted"] is False
    assert u.subscription_plan == "premium"
