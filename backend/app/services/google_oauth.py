"""Google OAuth helpers — real token exchange / id_token verify (no mocks)."""

from __future__ import annotations

import logging
import secrets
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_TOKENINFO = "https://oauth2.googleapis.com/tokeninfo"


def google_oauth_configured() -> bool:
    return bool((settings.GOOGLE_CLIENT_ID or "").strip() and (settings.GOOGLE_CLIENT_SECRET or "").strip())


def redirect_uri() -> str:
    if settings.GOOGLE_REDIRECT_URI:
        return settings.GOOGLE_REDIRECT_URI.rstrip("/")
    # Default: API callback under v1 auth
    base = settings.APP_URL.rstrip("/")
    # Prefer explicit API origin via env; fall back to APP_URL proxy path
    return f"{base}/api/v1/auth/google/callback"


def build_authorize_url(state: Optional[str] = None) -> tuple[str, str]:
    if not google_oauth_configured():
        raise RuntimeError("google_oauth_not_configured")
    st = state or secrets.token_urlsafe(24)
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "include_granted_scopes": "true",
        "prompt": "select_account",
        "state": st,
    }
    return f"{GOOGLE_AUTH}?{urlencode(params)}", st


async def exchange_code(code: str) -> Dict[str, Any]:
    """Exchange authorization code for tokens (requires client secret)."""
    if not google_oauth_configured():
        raise RuntimeError("google_oauth_not_configured")
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            GOOGLE_TOKEN,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri(),
                "grant_type": "authorization_code",
            },
        )
        if resp.status_code >= 400:
            logger.warning("Google token exchange failed: %s %s", resp.status_code, resp.text[:300])
            raise ValueError("token_exchange_failed")
        return resp.json()


async def fetch_userinfo(access_token: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(
            GOOGLE_USERINFO,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code >= 400:
            raise ValueError("userinfo_failed")
        return resp.json()


async def verify_id_token(id_token: str) -> Dict[str, Any]:
    """
    Verify a Google ID token via tokeninfo endpoint and audience check.

    Returns claims including sub, email, email_verified, given_name, family_name.
    """
    client_id = (settings.GOOGLE_CLIENT_ID or "").strip()
    if not client_id:
        raise RuntimeError("google_oauth_not_configured")
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(GOOGLE_TOKENINFO, params={"id_token": id_token})
        if resp.status_code >= 400:
            raise ValueError("invalid_id_token")
        data = resp.json()
    aud = data.get("aud")
    if aud != client_id:
        raise ValueError("audience_mismatch")
    if not data.get("email"):
        raise ValueError("email_required")
    # Google returns email_verified as string "true"/"false" sometimes
    verified = data.get("email_verified")
    if verified in (False, "false", "False", 0, "0"):
        raise ValueError("email_not_verified")
    return data
