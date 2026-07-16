"""Connect LinkedIn/Indeed → BoardSession → genuine Easy Apply E2E."""

from __future__ import annotations

import os
import threading
import uuid
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-32chars")
os.environ["HEADLESS_APPLY_AUTO_SUBMIT"] = "true"
os.environ["HEADLESS_APPLY_ENABLED"] = "true"

from app.core.config import settings

settings.HEADLESS_APPLY_AUTO_SUBMIT = True
settings.HEADLESS_APPLY_ENABLED = True

from app.main import app
from app.database import init_db, SessionLocal
from app.models.user import User
from app.models.job import Job, JobSource
from app.models.cv import CV
from app.services.board_session import cookies_to_storage_state, get_board_session


FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def client():
    init_db()
    db = SessionLocal()
    try:
        db.execute(
            __import__("sqlalchemy").text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS auto_apply_submit BOOLEAN DEFAULT FALSE"
            )
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    return TestClient(app)


@pytest.fixture(scope="module")
def fixture_server():
    handler = partial(SimpleHTTPRequestHandler, directory=str(FIXTURE_DIR))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()


def _auth(client, prefix="conn"):
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "ConnectPass123!",
            "first_name": "Casey",
            "last_name": "Connect",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "ConnectPass123!"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.patch(
        "/api/v1/apply-engine/settings",
        headers=headers,
        json={"auto_apply_submit": True},
    )
    return headers, email


def test_cookies_to_storage_state_requires_li_at():
    with pytest.raises(ValueError, match="li_at"):
        cookies_to_storage_state(
            [{"name": "lang", "value": "en", "domain": ".linkedin.com"}],
            "linkedin",
        )


def test_cookies_to_storage_state_ok():
    state = cookies_to_storage_state(
        [
            {
                "name": "li_at",
                "value": "fake-session-token",
                "domain": ".linkedin.com",
                "path": "/",
                "secure": True,
                "httpOnly": True,
                "sameSite": "no_restriction",
                "expirationDate": 2000000000,
            },
            {"name": "JSESSIONID", "value": "ajax:123", "domain": ".linkedin.com"},
        ],
        "linkedin",
    )
    assert state["cookies"]
    assert any(c["name"] == "li_at" for c in state["cookies"])
    assert state["cookies"][0]["sameSite"] in ("None", "Lax", "Strict")


def test_connect_status_and_from_cookies(client):
    headers, email = _auth(client, "cst")
    st = client.get("/api/v1/apply-engine/connect/status", headers=headers)
    assert st.status_code == 200
    body = st.json()
    assert body["extension_required"] is True
    assert body["boards"]["linkedin"]["connected"] is False

    bad = client.post(
        "/api/v1/apply-engine/board-sessions/linkedin/from-cookies",
        headers=headers,
        json={"cookies": [{"name": "foo", "value": "bar", "domain": ".linkedin.com"}]},
    )
    assert bad.status_code == 400

    ok = client.post(
        "/api/v1/apply-engine/board-sessions/linkedin/from-cookies",
        headers=headers,
        json={
            "cookies": [
                {
                    "name": "li_at",
                    "value": "test-li-at-token",
                    "domain": ".linkedin.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": True,
                }
            ],
            "label": "test-connect",
        },
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["connected"] is True
    assert ok.json()["cookie_count"] >= 1

    st2 = client.get("/api/v1/apply-engine/connect/status", headers=headers).json()
    assert st2["boards"]["linkedin"]["connected"] is True
    assert st2["boards"]["linkedin"]["has_auth_cookie"] is True

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        row = get_board_session(db, user.id, "linkedin")
        assert row is not None
        assert "li_at" in (row.storage_state_json or "")
    finally:
        db.close()


def test_connect_then_linkedin_easy_apply(client, fixture_server):
    """Full path: connect cookies → headless Easy Apply fixture submits."""
    headers, email = _auth(client, "e2e")
    client.post(
        "/api/v1/apply-engine/board-sessions/linkedin/from-cookies",
        headers=headers,
        json={
            "cookies": [
                {
                    "name": "li_at",
                    "value": "session-for-apply",
                    "domain": ".linkedin.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": True,
                }
            ]
        },
    )

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        src = db.query(JobSource).filter_by(name="linkedin").first()
        if not src:
            src = JobSource(name="linkedin", base_url="https://www.linkedin.com")
            db.add(src)
            db.commit()
            db.refresh(src)
        job = Job(
            source_id=src.id,
            external_id=f"li-e2e-{uuid.uuid4().hex[:8]}",
            external_url=f"{fixture_server}/ats_linkedin_easy_apply.html",
            title="Connect E2E Role",
            company="JobScaleTest",
            is_active=True,
        )
        db.add(job)
        db.add(
            CV(
                user_id=user.id,
                full_name="Casey Connect",
                email=email,
                phone="+15555550777",
                is_primary=True,
            )
        )
        db.commit()
        db.refresh(job)
        job_id = job.id
    finally:
        db.close()

    app_id = client.post(
        "/api/v1/applications/start", headers=headers, json={"job_id": job_id}
    ).json()["application_id"]

    # Package should show session present
    pkg = client.get(
        f"/api/v1/apply-engine/package/application/{app_id}", headers=headers
    ).json()
    assert pkg["ats"] == "linkedin"
    assert pkg["capabilities"]["needs_session"] is True
    assert pkg["capabilities"]["board_session"] is True

    body = client.post(
        "/api/v1/apply-engine/headless",
        headers=headers,
        json={"application_id": app_id, "dry_run": False, "auto_submit": True},
    ).json()
    assert body["ok"] is True, body
    assert body["submitted"] is True, body
    assert body.get("session_used") is True


def test_indeed_from_cookies(client):
    headers, _ = _auth(client, "indc")
    r = client.post(
        "/api/v1/apply-engine/board-sessions/indeed/from-cookies",
        headers=headers,
        json={
            "cookies": [
                {
                    "name": "PPID",
                    "value": "indeed-session",
                    "domain": ".indeed.com",
                    "path": "/",
                }
            ]
        },
    )
    assert r.status_code == 200, r.text
    st = client.get("/api/v1/apply-engine/connect/status", headers=headers).json()
    assert st["boards"]["indeed"]["connected"] is True


def test_live_linkedin_url_without_session_blocks_with_connect_hint(client):
    """Real linkedin.com host without Connect → needs_user + connect_hint (no silent fail)."""
    headers, email = _auth(client, "nosess")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        src = db.query(JobSource).filter_by(name="linkedin").first()
        if not src:
            src = JobSource(name="linkedin", base_url="https://www.linkedin.com")
            db.add(src)
            db.commit()
            db.refresh(src)
        job = Job(
            source_id=src.id,
            external_id=f"li-nosess-{uuid.uuid4().hex[:8]}",
            external_url="https://www.linkedin.com/jobs/view/1234567890",
            title="Needs Connect",
            company="JobScaleTest",
            is_active=True,
        )
        db.add(job)
        db.add(
            CV(
                user_id=user.id,
                full_name="Casey Connect",
                email=email,
                phone="+15555550777",
                is_primary=True,
            )
        )
        db.commit()
        db.refresh(job)
        job_id = job.id
    finally:
        db.close()

    app_id = client.post(
        "/api/v1/applications/start", headers=headers, json={"job_id": job_id}
    ).json()["application_id"]
    pkg = client.get(
        f"/api/v1/apply-engine/package/application/{app_id}", headers=headers
    ).json()
    assert pkg["ats"] == "linkedin"
    assert pkg["capabilities"]["needs_session"] is True
    assert pkg["capabilities"]["board_session"] is False
    assert pkg.get("connect_hint")

    body = client.post(
        "/api/v1/apply-engine/headless",
        headers=headers,
        json={"application_id": app_id, "dry_run": False, "auto_submit": True},
    ).json()
    assert body["ok"] is True
    assert body["submitted"] is False
    assert body["status"] == "needs_user"
    assert body.get("blocked_reason") == "login_required"
    assert body.get("connect_hint")
    assert body.get("session_used") is False
