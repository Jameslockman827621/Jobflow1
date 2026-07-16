"""Signed tokens for one-click email unsubscribe (no login required)."""

from __future__ import annotations

from datetime import timedelta

from app.core.config import settings
from app.core.security import create_access_token, verify_token


def make_unsubscribe_token(user_id: int) -> str:
    return create_access_token(
        data={"sub": str(user_id), "purpose": "unsubscribe_alerts"},
        expires_delta=timedelta(days=90),
    )


def parse_unsubscribe_token(token: str) -> int:
    payload = verify_token(token)
    if not payload or payload.get("purpose") != "unsubscribe_alerts":
        raise ValueError("invalid")
    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid") from exc


def unsubscribe_url(user_id: int) -> str:
    base = settings.APP_URL.rstrip("/")
    token = make_unsubscribe_token(user_id)
    return f"{base}/unsubscribe?token={token}"
