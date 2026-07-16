"""Workday + Ashby deeper fixture coverage (genuine submit on local fixtures)."""

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
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")
os.environ.setdefault("ALLOW_FIXTURE_SUBMIT", "true")

from app.core.config import settings

settings.RATE_LIMIT_PER_MINUTE = 0
settings.ALLOW_FIXTURE_SUBMIT = True

from app.main import app
from app.database import init_db, SessionLocal
from app.models.user import User
from app.models.job import Job, JobSource
from app.models.cv import CV

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


@pytest.fixture(scope="module")
def fixture_server():
    handler = partial(SimpleHTTPRequestHandler, directory=FIXTURE_DIR)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()


def _auth(client, prefix="wd"):
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "WorkAsh123!",
            "first_name": "Ada",
            "last_name": "Lovelace",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "WorkAsh123!"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.patch(
        "/api/v1/apply-engine/settings",
        headers=headers,
        json={"auto_apply_submit": True},
    )
    return headers, email


def _start_app(client, headers, email, url: str, source_name: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        src = db.query(JobSource).filter_by(name=source_name).first()
        if not src:
            src = JobSource(name=source_name, base_url=url)
            db.add(src)
            db.commit()
            db.refresh(src)
        job = Job(
            source_id=src.id,
            external_id=f"{source_name}-{uuid.uuid4().hex[:8]}",
            external_url=url,
            title=f"{source_name.title()} Fixture Role",
            company="JobScaleTest",
            is_active=True,
        )
        db.add(job)
        db.add(
            CV(
                user_id=user.id,
                full_name="Ada Lovelace",
                email=email,
                phone="+15555550123",
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
    return app_id


def test_workday_multistep_genuine_submit(client, fixture_server):
    headers, email = _auth(client, "wd")
    url = f"{fixture_server}/ats_workday_apply.html"
    app_id = _start_app(client, headers, email, url, "workday")
    body = client.post(
        "/api/v1/apply-engine/headless",
        headers=headers,
        json={"application_id": app_id, "dry_run": False, "auto_submit": True},
    ).json()
    assert body.get("ok") is True, body
    assert body.get("submitted") is True, body
    assert body.get("ats") == "workday" or body.get("adapter") == "workday"


def test_ashby_multistep_genuine_submit(client, fixture_server):
    headers, email = _auth(client, "ash")
    url = f"{fixture_server}/ats_ashby_apply.html"
    app_id = _start_app(client, headers, email, url, "ashby")
    body = client.post(
        "/api/v1/apply-engine/headless",
        headers=headers,
        json={"application_id": app_id, "dry_run": False, "auto_submit": True},
    ).json()
    assert body.get("ok") is True, body
    assert body.get("submitted") is True, body
    assert body.get("ats") == "ashby" or body.get("adapter") == "ashby"
