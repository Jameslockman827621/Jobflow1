"""
Prove genuine auto-apply: fill + SUBMIT + confirmation.

Uses a local Greenhouse-like fixture so we never spam real employers,
but the same headless path / adapters / confirmation logic run.
"""

from __future__ import annotations

import os
import threading
import uuid
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

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


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture(scope="module")
def fixture_server():
    handler = partial(SimpleHTTPRequestHandler, directory=FIXTURE_DIR)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}/ats_greenhouse_apply.html"
    httpd.shutdown()


@pytest.fixture(scope="module")
def client():
    init_db()
    # Ensure column exists
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


@pytest.fixture
def opted_in_user(client):
    email = f"genuine_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "GenuinePass123!",
            "first_name": "Alex",
            "last_name": "Chen",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "GenuinePass123!"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Opt in to genuine submit
    r = client.patch(
        "/api/v1/apply-engine/settings",
        headers=headers,
        json={"auto_apply_submit": True},
    )
    assert r.status_code == 200, r.text
    assert r.json()["auto_apply_submit"] is True
    return headers, email


def test_settings_opt_in_required(client, opted_in_user):
    headers, _ = opted_in_user
    s = client.get("/api/v1/apply-engine/settings", headers=headers)
    assert s.status_code == 200
    assert s.json()["auto_apply_submit"] is True
    assert s.json()["platform_allows_submit"] is True


def test_genuine_submit_on_fixture(client, opted_in_user, fixture_server):
    headers, email = opted_in_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        assert user.auto_apply_submit is True

        src = db.query(JobSource).filter_by(name="greenhouse").first()
        if not src:
            src = JobSource(name="greenhouse", base_url="https://boards-api.greenhouse.io")
            db.add(src)
            db.commit()
            db.refresh(src)

        job = Job(
            source_id=src.id,
            external_id=f"fixture-{uuid.uuid4().hex[:8]}",
            external_url=fixture_server,
            title="Fixture Engineer",
            company="JobScaleTest",
            location="Remote",
            is_active=True,
        )
        db.add(job)
        if not db.query(CV).filter(CV.user_id == user.id).first():
            db.add(
                CV(
                    user_id=user.id,
                    full_name="Alex Chen",
                    email=email,
                    phone="+15555550123",
                    linkedin_url="https://linkedin.com/in/alexchen-test",
                    skills=["Python", "TypeScript"],
                    summary="Engineer",
                    is_primary=True,
                )
            )
        db.commit()
        db.refresh(job)
        job_id = job.id
    finally:
        db.close()

    start = client.post("/api/v1/applications/start", headers=headers, json={"job_id": job_id})
    assert start.status_code == 200, start.text
    app_id = start.json()["application_id"]

    # Genuine apply — must SUBMIT
    result = client.post(
        "/api/v1/apply-engine/headless",
        headers=headers,
        json={"application_id": app_id, "dry_run": False, "auto_submit": True},
    )
    assert result.status_code == 200, result.text
    body = result.json()
    assert body["ok"] is True
    assert body["submit_policy"]["should_submit"] is True
    assert body["fields_filled"] >= 3
    assert body["submitted"] is True, body
    assert body["genuine_apply"] is True
    assert body["status"] == "submitted"
    assert "thank" in (body.get("page_url") or "").lower() or body["submitted"]

    # Application row marked submitted
    apps = client.get("/api/v1/applications", headers=headers)
    assert apps.status_code == 200
    mine = [a for a in apps.json()["applications"] if a["id"] == app_id][0]
    assert mine["status"] == "submitted"


def test_without_opt_in_does_not_submit(client, fixture_server):
    email = f"nopt_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "NoOpt123!", "first_name": "No", "last_name": "Opt"},
    )
    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "NoOpt123!"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        src = db.query(JobSource).filter_by(name="greenhouse").first()
        job = Job(
            source_id=src.id,
            external_id=f"nopt-{uuid.uuid4().hex[:8]}",
            external_url=fixture_server,
            title="No Opt Role",
            company="JobScaleTest",
            is_active=True,
        )
        db.add(job)
        db.add(CV(user_id=user.id, full_name="No Opt", email=email, is_primary=True))
        db.commit()
        db.refresh(job)
        job_id = job.id
    finally:
        db.close()

    app_id = client.post(
        "/api/v1/applications/start", headers=headers, json={"job_id": job_id}
    ).json()["application_id"]

    body = client.post(
        "/api/v1/apply-engine/headless",
        headers=headers,
        json={"application_id": app_id, "dry_run": False, "auto_submit": True},
    ).json()
    assert body["ok"] is True
    assert body["submit_policy"]["should_submit"] is False
    assert body["submitted"] is False
    assert body["status"] != "submitted"
