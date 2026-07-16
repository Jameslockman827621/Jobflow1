"""World-class genuine apply: multi-step, PDF resume, confirmation strictness, fan-out."""

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
from app.services.resume_files import build_minimal_pdf, is_real_pdf, write_resume_file
from app.services.ats_adapters.submit import detect_submission_success
from app.tasks.headless_apply_tasks import apply_batch


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


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
def multistep_server():
    handler = partial(SimpleHTTPRequestHandler, directory=FIXTURE_DIR)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}/ats_greenhouse_multistep.html"
    httpd.shutdown()


def _opt_in(client, email_prefix="wc"):
    email = f"{email_prefix}_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "WorldClass123!",
            "first_name": "Alex",
            "last_name": "Chen",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "WorldClass123!"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.patch(
        "/api/v1/apply-engine/settings",
        headers=headers,
        json={"auto_apply_submit": True},
    )
    return headers, email


def test_real_pdf_resume_bytes():
    pdf = build_minimal_pdf("Alex Chen\nEngineer\nPython")
    assert pdf.startswith(b"%PDF-")
    path = write_resume_file(
        999001,
        {"full_name": "Alex Chen", "email": "a@example.com", "phone": "+15555550111"},
        None,
    )
    assert path.endswith(".pdf")
    assert is_real_pdf(path)
    with open(path, "rb") as f:
        assert f.read(5) == b"%PDF-"


def test_confirmation_requires_thank_you_pattern():
    class FakePage:
        url = "https://example.com/apply?x=1"

        async def inner_text(self, _sel):
            return "Please fix the errors below and try again."

        async def locator(self, _sel):
            class L:
                async def count(self):
                    return 1

            return L()

    import asyncio

    result = asyncio.run(detect_submission_success(FakePage()))
    assert result["confirmed"] is False


def test_multistep_genuine_submit(client, multistep_server):
    headers, email = _opt_in(client, "multi")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        src = db.query(JobSource).filter_by(name="greenhouse").first()
        if not src:
            src = JobSource(name="greenhouse", base_url="https://boards-api.greenhouse.io")
            db.add(src)
            db.commit()
            db.refresh(src)
        job = Job(
            source_id=src.id,
            external_id=f"ms-{uuid.uuid4().hex[:8]}",
            external_url=multistep_server,
            title="Multi Step Engineer",
            company="JobScaleTest",
            is_active=True,
        )
        db.add(job)
        db.add(
            CV(
                user_id=user.id,
                full_name="Alex Chen",
                email=email,
                phone="+15555550123",
                skills=["Python"],
                is_primary=True,
            )
        )
        db.commit()
        db.refresh(job)
        job_id = job.id
        user_id = user.id
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
    assert body["ok"] is True, body
    assert body["submitted"] is True, body
    assert body["genuine_apply"] is True
    assert body.get("steps_completed", 0) >= 1

    # PDF export endpoint
    cvs = client.get("/api/v1/cvs", headers=headers).json()["cvs"]
    assert cvs
    pdf_resp = client.get(f"/api/v1/cvs/{cvs[0]['id']}/pdf", headers=headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.content[:5] == b"%PDF-"
    assert "application/pdf" in pdf_resp.headers.get("content-type", "")


def test_batch_fans_out_tasks(monkeypatch):
    queued = []

    class FakeAsyncResult:
        def __init__(self, tid):
            self.id = tid

    def fake_delay(*args, **kwargs):
        tid = f"task-{len(queued)+1}"
        queued.append({"args": args, "kwargs": kwargs, "id": tid})
        return FakeAsyncResult(tid)

    monkeypatch.setattr(
        "app.tasks.headless_apply_tasks.apply_one.delay", fake_delay
    )
    out = apply_batch(1, [10, 11, 12], auto_submit=True, dry_run=False, max_per_batch=50)
    assert out["fan_out"] is True
    assert out["total"] == 3
    assert len(queued) == 3


def test_settings_exposes_genuine_ready(client):
    headers, _ = _opt_in(client, "ready")
    s = client.get("/api/v1/apply-engine/settings", headers=headers).json()
    assert "profile_completeness" in s
    assert "genuine_ready" in s
    assert s["auto_apply_submit"] is True


def test_retry_endpoint_queues(client, monkeypatch):
    headers, email = _opt_in(client, "retry")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        src = db.query(JobSource).filter_by(name="greenhouse").first()
        job = Job(
            source_id=src.id,
            external_id=f"retry-{uuid.uuid4().hex[:8]}",
            external_url="https://boards.greenhouse.io/example/jobs/1",
            title="Retry Role",
            company="JobScaleTest",
            is_active=True,
        )
        db.add(job)
        db.add(CV(user_id=user.id, full_name="Alex Chen", email=email, phone="+15555550123", is_primary=True))
        db.commit()
        db.refresh(job)
        job_id = job.id
    finally:
        db.close()

    app_id = client.post(
        "/api/v1/applications/start", headers=headers, json={"job_id": job_id}
    ).json()["application_id"]

    # Seed a failed ApplyRun
    from app.models.company import ApplyRun
    from datetime import datetime

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        db.add(
            ApplyRun(
                user_id=user.id,
                application_id=app_id,
                job_id=job_id,
                mode="headless",
                ats_type="greenhouse",
                status="failed",
                started_at=datetime.utcnow(),
                finished_at=datetime.utcnow(),
                error="timeout",
            )
        )
        db.commit()
    finally:
        db.close()

    queued = []

    class FakeAsyncResult:
        id = "batch-retry-1"

    def fake_batch_delay(*a, **k):
        queued.append((a, k))
        return FakeAsyncResult()

    monkeypatch.setattr("app.api.apply_engine.apply_batch.delay", fake_batch_delay)
    r = client.post(
        "/api/v1/apply-engine/headless/retry",
        headers=headers,
        json={"auto_submit": True, "limit": 10},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["queued"] >= 1
    assert app_id in body["application_ids"]
    assert queued
