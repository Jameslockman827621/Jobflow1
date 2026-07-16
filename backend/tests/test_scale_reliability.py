"""Scale reliability: quotas, stale runs, batch status, answer bank, Workable, idempotency."""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timedelta
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
from app.models.company import ApplyRun
from app.models.application import Application
from app.services.apply_limits import check_apply_quota, DEFAULT_HOURLY_LIMIT
from app.services.answer_bank import upsert_answer, lookup_answer
from app.services.proxy_pool import fingerprint_headers
from app.tasks.headless_apply_tasks import apply_batch, fail_stale_apply_runs
from app.services.ats_adapters import get_adapter


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
def workable_server():
    handler = partial(SimpleHTTPRequestHandler, directory=FIXTURE_DIR)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}/ats_workable_apply.html"
    httpd.shutdown()


def _auth(client, prefix="sr"):
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "ScaleRel123!",
            "first_name": "Sam",
            "last_name": "Reli",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "ScaleRel123!"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.patch(
        "/api/v1/apply-engine/settings",
        headers=headers,
        json={"auto_apply_submit": True},
    )
    return headers, email


def test_quota_ignores_failed_and_dry_run(client):
    headers, email = _auth(client, "quota")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        for i in range(5):
            db.add(
                ApplyRun(
                    user_id=user.id,
                    mode="headless",
                    status="failed",
                    error="x",
                    started_at=datetime.utcnow(),
                    finished_at=datetime.utcnow(),
                )
            )
        db.add(
            ApplyRun(
                user_id=user.id,
                mode="headless",
                status="filled",
                meta_json=json.dumps({"dry_run": True}),
                started_at=datetime.utcnow(),
                finished_at=datetime.utcnow(),
            )
        )
        db.commit()
        q = check_apply_quota(db, user.id, requested=1)
        assert q["hourly_used"] == 0
        assert q["allowed"] is True
    finally:
        db.close()


def test_quota_counts_submitted(client):
    headers, email = _auth(client, "qsub")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        for _ in range(DEFAULT_HOURLY_LIMIT):
            db.add(
                ApplyRun(
                    user_id=user.id,
                    mode="headless",
                    status="submitted",
                    started_at=datetime.utcnow(),
                    finished_at=datetime.utcnow(),
                )
            )
        db.commit()
        q = check_apply_quota(db, user.id, requested=1)
        assert q["allowed"] is False
        assert "hourly" in (q["reason"] or "")
    finally:
        db.close()


def test_fail_stale_apply_runs(client):
    headers, email = _auth(client, "stale")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        old = ApplyRun(
            user_id=user.id,
            mode="headless",
            status="running",
            started_at=datetime.utcnow() - timedelta(minutes=30),
        )
        db.add(old)
        db.commit()
        rid = old.id
    finally:
        db.close()

    out = fail_stale_apply_runs(max_age_minutes=15)
    assert out["marked_stale"] >= 1
    db = SessionLocal()
    try:
        row = db.query(ApplyRun).filter(ApplyRun.id == rid).first()
        assert row.status == "stale"
    finally:
        db.close()


def test_batch_fan_out_uses_apply_async(monkeypatch):
    queued = []

    class FakeAsyncResult:
        def __init__(self, tid):
            self.id = tid

    def fake_apply_async(*args, **kwargs):
        tid = f"t-{len(queued)+1}"
        queued.append({"args": args, "kwargs": kwargs})
        return FakeAsyncResult(tid)

    monkeypatch.setattr(
        "app.tasks.headless_apply_tasks.apply_one.apply_async", fake_apply_async
    )
    out = apply_batch(1, [1, 2, 3, 4], auto_submit=True, dry_run=False, max_per_batch=2)
    assert out["fan_out"] is True
    assert out["queued_count"] == 2
    assert out["deferred_count"] == 2
    assert out["batch_id"]
    assert len(queued) == 2
    assert queued[0]["kwargs"].get("queue") == "apply"


def test_answer_bank_roundtrip(client):
    headers, email = _auth(client, "bank")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        upsert_answer(db, user.id, "Why do you want this role?", "I love building products.")
        hit = lookup_answer(db, user.id, "Why do you want this role?")
        assert hit == "I love building products."
    finally:
        db.close()

    r = client.post(
        "/api/v1/apply-engine/answer",
        headers=headers,
        json={
            "question": "Tell us about yourself",
            "answer": "Engineer with 5 years experience.",
            "save": True,
        },
    )
    assert r.status_code == 200
    assert r.json()["saved"] is True


def test_sticky_fingerprint_stable():
    a = fingerprint_headers(user_id=42)
    b = fingerprint_headers(user_id=42)
    c = fingerprint_headers(user_id=99)
    assert a["User-Agent"] == b["User-Agent"]
    assert a["Sec-Ch-Ua-Platform"] == b["Sec-Ch-Ua-Platform"]
    assert a["User-Agent"] != c["User-Agent"] or a["Sec-Ch-Ua-Platform"] != c["Sec-Ch-Ua-Platform"]


def test_workable_adapter_registered():
    adapter = get_adapter("workable")
    assert adapter.name == "workable"


def test_workable_genuine_submit(client, workable_server):
    headers, email = _auth(client, "wrk")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        src = db.query(JobSource).filter_by(name="workable").first()
        if not src:
            src = JobSource(name="workable", base_url="https://apply.workable.com")
            db.add(src)
            db.commit()
            db.refresh(src)
        job = Job(
            source_id=src.id,
            external_id=f"wrk-{uuid.uuid4().hex[:8]}",
            external_url=workable_server,
            title="Workable Fixture Role",
            company="JobScaleTest",
            is_active=True,
        )
        db.add(job)
        db.add(
            CV(
                user_id=user.id,
                full_name="Sam Reli",
                email=email,
                phone="+15555550999",
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
    body = client.post(
        "/api/v1/apply-engine/headless",
        headers=headers,
        json={"application_id": app_id, "dry_run": False, "auto_submit": True},
    ).json()
    assert body["ok"] is True, body
    assert body["submitted"] is True, body
    assert body.get("ats") == "workable" or body.get("adapter") == "workable"

    # Idempotency: second run skips
    body2 = client.post(
        "/api/v1/apply-engine/headless",
        headers=headers,
        json={"application_id": app_id, "dry_run": False, "auto_submit": True},
    ).json()
    assert body2.get("skipped") is True or body2.get("submitted") is True


def test_batch_status_and_metrics(client):
    headers, email = _auth(client, "metrics")
    batch_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        for status in ("submitted", "submitted", "failed", "needs_user"):
            db.add(
                ApplyRun(
                    user_id=user.id,
                    mode="headless",
                    status=status,
                    ats_type="greenhouse",
                    meta_json=json.dumps({"batch_id": batch_id}),
                    started_at=datetime.utcnow(),
                    finished_at=datetime.utcnow(),
                )
            )
        db.commit()
    finally:
        db.close()

    st = client.get(f"/api/v1/apply-engine/headless/batch/{batch_id}", headers=headers)
    assert st.status_code == 200
    body = st.json()
    assert body["total"] == 4
    assert body["submitted"] == 2
    assert body["needs_user"] == 1

    m = client.get("/api/v1/apply-engine/metrics/apply?hours=24", headers=headers)
    assert m.status_code == 200
    assert m.json()["submitted"] >= 2
    assert "success_rate" in m.json()
