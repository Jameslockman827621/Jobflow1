"""Stripe webhook plan sync — mocked signatures, no live Stripe."""

from __future__ import annotations

import json
import os
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-32chars")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_secret_for_unit_tests"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_unit_not_real"
os.environ["STRIPE_PRICE_PRO_MONTHLY"] = "price_pro_monthly_test"
os.environ["STRIPE_PRICE_PREMIUM_MONTHLY"] = "price_premium_monthly_test"

from app.core.config import settings

settings.RATE_LIMIT_PER_MINUTE = 0
settings.STRIPE_WEBHOOK_SECRET = os.environ["STRIPE_WEBHOOK_SECRET"]
settings.STRIPE_SECRET_KEY = os.environ["STRIPE_SECRET_KEY"]
settings.STRIPE_PRICE_PRO_MONTHLY = os.environ["STRIPE_PRICE_PRO_MONTHLY"]
settings.STRIPE_PRICE_PREMIUM_MONTHLY = os.environ["STRIPE_PRICE_PREMIUM_MONTHLY"]

from app.main import app
from app.database import init_db, SessionLocal
from app.models.user import User
from app.core.security import get_password_hash


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


def _user(email: str | None = None, **kwargs) -> User:
    db = SessionLocal()
    try:
        u = User(
            email=email or f"bill_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password=get_password_hash("TestPass123!"),
            is_active=True,
            subscription_plan=kwargs.get("subscription_plan", "free"),
            subscription_status=kwargs.get("subscription_status", "active"),
            stripe_customer_id=kwargs.get("stripe_customer_id"),
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        db.expunge(u)
        return u
    finally:
        db.close()


def _post_event(client: TestClient, event: dict):
    payload = json.dumps(event).encode()

    def _construct(payload_in, sig, secret):
        assert secret == settings.STRIPE_WEBHOOK_SECRET
        return event

    with patch("stripe.Webhook.construct_event", side_effect=_construct):
        return client.post(
            "/api/v1/billing/webhook",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "t=1,v1=fake",
            },
        )


def test_webhook_503_without_secret(client, monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", None)
    r = client.post("/api/v1/billing/webhook", data=b"{}")
    assert r.status_code == 503
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", os.environ["STRIPE_WEBHOOK_SECRET"])


def test_checkout_completed_sets_pro_plan(client):
    user = _user()
    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"user_id": str(user.id), "plan": "pro_monthly"},
                "customer": f"cus_{uuid.uuid4().hex[:10]}",
            }
        },
    }
    r = _post_event(client, event)
    assert r.status_code == 200, r.text

    db = SessionLocal()
    try:
        u = db.query(User).filter(User.id == user.id).first()
        assert u.subscription_plan == "pro"
        assert u.subscription_status == "active"
        assert u.stripe_customer_id.startswith("cus_")
    finally:
        db.close()


def test_subscription_updated_maps_premium_price(client):
    cust = f"cus_{uuid.uuid4().hex[:10]}"
    user = _user(stripe_customer_id=cust, subscription_plan="free")
    event = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "customer": cust,
                "status": "active",
                "current_period_end": 1893456000,
                "items": {
                    "data": [
                        {
                            "price": {
                                "id": settings.STRIPE_PRICE_PREMIUM_MONTHLY,
                                "nickname": "Premium Monthly",
                                "metadata": {},
                            }
                        }
                    ]
                },
            }
        },
    }
    r = _post_event(client, event)
    assert r.status_code == 200, r.text

    db = SessionLocal()
    try:
        u = db.query(User).filter(User.id == user.id).first()
        assert u.subscription_plan == "premium"
        assert u.subscription_status == "active"
        assert u.subscription_end is not None
    finally:
        db.close()


def test_subscription_deleted_reverts_to_free(client):
    cust = f"cus_{uuid.uuid4().hex[:10]}"
    user = _user(stripe_customer_id=cust, subscription_plan="pro")
    event = {
        "type": "customer.subscription.deleted",
        "data": {"object": {"customer": cust}},
    }
    r = _post_event(client, event)
    assert r.status_code == 200, r.text

    db = SessionLocal()
    try:
        u = db.query(User).filter(User.id == user.id).first()
        assert u.subscription_plan == "free"
        assert u.subscription_status == "cancelled"
    finally:
        db.close()
