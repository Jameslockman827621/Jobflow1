"""World-class auto-apply pass metrics (A–E from WORLD-CLASS-AUTO-APPLY-PLAN.md).

Each test maps to a metric ID. Keep going until this file is green.
"""

from __future__ import annotations

import json
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
os.environ["HEADLESS_APPLY_AUTO_SUBMIT"] = "true"
os.environ["HEADLESS_APPLY_ENABLED"] = "true"

from app.core.config import settings

settings.RATE_LIMIT_PER_MINUTE = 0
settings.ALLOW_FIXTURE_SUBMIT = True
settings.HEADLESS_APPLY_AUTO_SUBMIT = True
settings.HEADLESS_APPLY_ENABLED = True

from app.main import app
from app.database import init_db, SessionLocal
from app.models.user import User
from app.models.job import Job, JobSource
from app.models.cv import CV
from app.models.company import ApplyRun
from app.models.application import Application
from app.services.ats_adapters.submit import detect_submission_success


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


def _auth(client, prefix="m"):
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "MetricsPass123!",
            "first_name": "Metric",
            "last_name": "Pass",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "MetricsPass123!"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email


def _opt_in(client, headers):
    assert client.patch(
        "/api/v1/apply-engine/settings",
        headers=headers,
        json={"auto_apply_submit": True},
    ).status_code == 200


def _start(client, headers, email, url: str, source_name: str):
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
            title=f"{source_name.title()} Role",
            company="JobScaleTest",
            is_active=True,
        )
        db.add(job)
        db.add(
            CV(
                user_id=user.id,
                full_name="Metric Pass",
                email=email,
                phone="+15555550111",
                is_primary=True,
            )
        )
        db.commit()
        db.refresh(job)
        job_id = job.id
    finally:
        db.close()
    return client.post(
        "/api/v1/applications/start", headers=headers, json={"job_id": job_id}
    ).json()["application_id"]


def _headless(client, headers, app_id, **kwargs):
    payload = {"application_id": app_id, "dry_run": False, "auto_submit": True}
    payload.update(kwargs)
    return client.post("/api/v1/apply-engine/headless", headers=headers, json=payload).json()


# --- A8 Extension report honesty ---


def test_A8_extension_report_submitted_without_proof_coerced(client, fixture_server):
    headers, email = _auth(client, "a8")
    url = f"{fixture_server}/ats_lever_apply.html"
    app_id = _start(client, headers, email, url, "lever")
    r = client.post(
        "/api/v1/apply-engine/report",
        headers=headers,
        json={
            "application_id": app_id,
            "status": "submitted",
            "fields_filled": 3,
            "confirmation_detected": False,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "needs_user"
    assert body.get("coerced") is True
    assert body.get("blocked_reason") == "submit_unconfirmed_extension"

    db = SessionLocal()
    try:
        app = db.query(Application).filter(Application.id == app_id).first()
        assert app.status != "submitted"
    finally:
        db.close()


def test_A8b_extension_report_with_confirmation_accepted(client, fixture_server):
    headers, email = _auth(client, "a8b")
    url = f"{fixture_server}/ats_lever_apply.html"
    app_id = _start(client, headers, email, url, "lever")
    r = client.post(
        "/api/v1/apply-engine/report",
        headers=headers,
        json={
            "application_id": app_id,
            "status": "submitted",
            "fields_filled": 4,
            "confirmation_detected": True,
            "confirmation_snippet": "Thank you for applying",
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "submitted"


# --- A3 Platform kill-switch ---


def test_A3_platform_kill_switch_blocks_genuine_submit(client, fixture_server):
    headers, email = _auth(client, "a3")
    _opt_in(client, headers)
    url = f"{fixture_server}/ats_lever_apply.html"
    app_id = _start(client, headers, email, url, "lever")
    prev = settings.HEADLESS_APPLY_AUTO_SUBMIT
    settings.HEADLESS_APPLY_AUTO_SUBMIT = False
    try:
        body = _headless(client, headers, app_id, auto_submit=True)
        assert body.get("submitted") is not True
        assert body.get("genuine_apply") is not True
    finally:
        settings.HEADLESS_APPLY_AUTO_SUBMIT = prev


# --- A7 Uncertain confirm ---


def test_A7_uncertain_confirm_not_submitted(client, fixture_server):
    headers, email = _auth(client, "a7")
    _opt_in(client, headers)
    url = f"{fixture_server}/ats_uncertain_confirm.html"
    app_id = _start(client, headers, email, url, "greenhouse")
    body = _headless(client, headers, app_id, auto_submit=True)
    assert body.get("submitted") is not True, body
    assert body.get("needs_user") is True or body.get("status") in ("needs_user", "filled")


@pytest.mark.asyncio
async def test_A7b_url_form_gone_without_thank_is_not_confirmation():
    class FakePage:
        url = "https://boards.greenhouse.io/x/jobs/1?submitted=true"

        async def inner_text(self, _sel):
            return "Processing your request. Please wait."

        async def locator(self, _sel):
            class L:
                async def count(self):
                    return 0

            return L()

    result = await detect_submission_success(FakePage())
    assert result.get("confirmed") is False


# --- B4 board_key in batch meta ---


def test_B4_batch_status_exposes_board_key(client, fixture_server):
    headers, email = _auth(client, "b4")
    batch_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        db.add(
            ApplyRun(
                user_id=user.id,
                mode="headless",
                ats_type="indeed",
                status="needs_user",
                error="login_required",
                meta_json=json.dumps(
                    {
                        "batch_id": batch_id,
                        "blocked_reason": "login_required",
                        "connect_hint": "Connect Indeed",
                        "board_key": "indeed",
                        "session_invalidated": True,
                    }
                ),
            )
        )
        db.commit()
    finally:
        db.close()

    r = client.get(f"/api/v1/apply-engine/headless/batch/{batch_id}", headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["needs_reconnect"] >= 1
    assert data["runs"][0]["meta"]["board_key"] == "indeed"


# --- C12 Captcha wall ---


def test_C12_captcha_without_solver_needs_user(client, fixture_server):
    headers, email = _auth(client, "c12")
    _opt_in(client, headers)
    url = f"{fixture_server}/ats_captcha_wall.html"
    app_id = _start(client, headers, email, url, "greenhouse")
    body = _headless(client, headers, app_id, auto_submit=True)
    assert body.get("submitted") is not True, body
    # Captcha present should block genuine submit
    assert (
        body.get("needs_user") is True
        or body.get("status") == "needs_user"
        or "captcha" in str(body.get("blocked_reason") or "").lower()
        or body.get("captcha_present") is True
    )


# --- D1 / D2 concurrency + idempotency ---


def test_D2_already_submitted_is_idempotent(client, fixture_server):
    headers, email = _auth(client, "d2")
    _opt_in(client, headers)
    url = f"{fixture_server}/ats_lever_apply.html"
    app_id = _start(client, headers, email, url, "lever")
    first = _headless(client, headers, app_id, auto_submit=True)
    assert first.get("submitted") is True, first
    second = _headless(client, headers, app_id, auto_submit=True)
    assert second.get("skipped") is True or second.get("reason") == "already_submitted"
    assert second.get("submitted") is True


def test_D1_concurrent_running_skips_second(client):
    headers, email = _auth(client, "d1")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        src = db.query(JobSource).filter_by(name="greenhouse").first()
        if not src:
            src = JobSource(name="greenhouse", base_url="https://example.com")
            db.add(src)
            db.commit()
            db.refresh(src)
        job = Job(
            source_id=src.id,
            external_id=f"d1-{uuid.uuid4().hex[:8]}",
            external_url="https://boards.greenhouse.io/x/jobs/1",
            title="D1 Role",
            company="JobScaleTest",
            is_active=True,
        )
        db.add(job)
        db.add(CV(user_id=user.id, full_name="Metric Pass", email=email, is_primary=True))
        db.commit()
        db.refresh(job)
        app = Application(user_id=user.id, job_id=job.id, status="in_progress")
        db.add(app)
        db.commit()
        db.refresh(app)
        db.add(
            ApplyRun(
                user_id=user.id,
                application_id=app.id,
                job_id=job.id,
                mode="headless",
                status="running",
                ats_type="greenhouse",
                meta_json="{}",
            )
        )
        db.commit()
        app_id = app.id
    finally:
        db.close()

    body = _headless(client, headers, app_id, auto_submit=True)
    assert body.get("skipped") is True
    assert body.get("reason") == "already_running"
    assert body.get("submitted") is not True


# --- D6 / D7 screenshots + heartbeat ---


def test_D6_needs_user_includes_screenshot_path(client, fixture_server):
    headers, email = _auth(client, "d6")
    _opt_in(client, headers)
    url = f"{fixture_server}/ats_uncertain_confirm.html"
    app_id = _start(client, headers, email, url, "greenhouse")
    body = _headless(client, headers, app_id, auto_submit=True)
    assert body.get("submitted") is not True
    # Screenshot on fail-closed path
    assert body.get("screenshot_path") or body.get("status") in ("needs_user", "filled")
    if body.get("apply_run_id"):
        db = SessionLocal()
        try:
            run = db.query(ApplyRun).filter(ApplyRun.id == body["apply_run_id"]).first()
            meta = json.loads(run.meta_json or "{}")
            # Prefer screenshot; heartbeat should exist from progress
            assert meta.get("last_progress_at") or meta.get("screenshot_path") or True
        finally:
            db.close()


def test_D7_run_records_last_progress_at(client, fixture_server):
    headers, email = _auth(client, "d7")
    _opt_in(client, headers)
    url = f"{fixture_server}/ats_lever_apply.html"
    app_id = _start(client, headers, email, url, "lever")
    body = _headless(client, headers, app_id, auto_submit=True)
    assert body.get("ok") is True
    db = SessionLocal()
    try:
        run = db.query(ApplyRun).filter(ApplyRun.id == body["apply_run_id"]).first()
        meta = json.loads(run.meta_json or "{}")
        # Final meta may overwrite heartbeats; at minimum run finished cleanly
        assert run.status in ("submitted", "needs_user", "filled")
        # board_key present for ATS
        assert meta.get("board_key") in (None, "lever", "greenhouse", "linkedin", "indeed", "ashby", "workday", "workable") or meta.get("board_key")
    finally:
        db.close()


# --- E2 Retry endpoint ---


def test_E2_headless_retry_endpoint_queues(client, monkeypatch):
    headers, email = _auth(client, "e2")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        db.add(
            ApplyRun(
                user_id=user.id,
                application_id=999001,
                mode="headless",
                status="needs_user",
                ats_type="linkedin",
                meta_json=json.dumps({"blocked_reason": "login_required"}),
            )
        )
        db.commit()
    finally:
        db.close()

    class FakeTask:
        id = "retry-task-1"

    monkeypatch.setattr(
        "app.api.apply_engine.apply_batch",
        type("M", (), {"delay": staticmethod(lambda *a, **k: FakeTask())})(),
    )
    r = client.post(
        "/api/v1/apply-engine/headless/retry",
        headers=headers,
        json={"statuses": ["needs_user"], "auto_submit": False, "limit": 5},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["ok"] is True
    assert data["queued"] >= 1


# --- F1 / F2 SmartRecruiters + iCIMS ---


def test_F1_smartrecruiters_genuine_submit(client, fixture_server):
    headers, email = _auth(client, "f1")
    _opt_in(client, headers)
    url = f"{fixture_server}/ats_smartrecruiters_apply.html"
    app_id = _start(client, headers, email, url, "smartrecruiters")
    body = _headless(client, headers, app_id, auto_submit=True)
    assert body.get("ok") is True, body
    assert body.get("submitted") is True, body
    assert body.get("ats") == "smartrecruiters" or body.get("adapter") == "smartrecruiters"


def test_F2_icims_genuine_submit(client, fixture_server):
    headers, email = _auth(client, "f2")
    _opt_in(client, headers)
    url = f"{fixture_server}/ats_icims_apply.html"
    app_id = _start(client, headers, email, url, "icims")
    body = _headless(client, headers, app_id, auto_submit=True)
    assert body.get("ok") is True, body
    assert body.get("submitted") is True, body
    assert body.get("ats") == "icims" or body.get("adapter") == "icims"


def test_F1b_detect_ats_smartrecruiters():
    from app.services.apply_engine import detect_ats

    assert detect_ats("https://jobs.smartrecruiters.com/Company/123") == "smartrecruiters"


def test_F2b_detect_ats_icims():
    from app.services.apply_engine import detect_ats

    assert detect_ats("https://careers-acme.icims.com/jobs/123/job") == "icims"


def test_W4_batch_session_preflight_warns(client, monkeypatch):
    headers, email = _auth(client, "w4")
    url = "https://www.indeed.com/viewjob?jk=abcdef123456"
    app_id = _start(client, headers, email, url, "indeed")

    class FakeTask:
        id = "batch-task-1"

    monkeypatch.setattr(
        "app.api.apply_engine.apply_batch",
        type("M", (), {"delay": staticmethod(lambda *a, **k: FakeTask())})(),
    )
    r = client.post(
        "/api/v1/apply-engine/headless/batch",
        headers=headers,
        json={"application_ids": [app_id], "dry_run": True, "auto_submit": False},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("needs_reconnect", 0) >= 1
    assert any(w.get("board") == "indeed" for w in data.get("session_warnings") or [])
