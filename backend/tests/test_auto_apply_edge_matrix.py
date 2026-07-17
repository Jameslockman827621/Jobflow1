"""Auto-apply reliability edge-case matrix — fixtures only, no live ToS boards.

Covers: opt-in gates, ATS adapters, confirmation honesty, quota soft-blocks,
batch meta/reconnect, resume gate when file input present, Lever parity.
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
from app.services.apply_limits import check_apply_quota
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


def _auth(client, prefix="aa"):
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "AutoApply123!",
            "first_name": "Auto",
            "last_name": "Apply",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "AutoApply123!"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return headers, email


def _opt_in(client, headers):
    r = client.patch(
        "/api/v1/apply-engine/settings",
        headers=headers,
        json={"auto_apply_submit": True},
    )
    assert r.status_code == 200, r.text


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
                full_name="Auto Apply",
                email=email,
                phone="+15555550199",
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


def _headless(client, headers, app_id, *, auto_submit=True, dry_run=False):
    return client.post(
        "/api/v1/apply-engine/headless",
        headers=headers,
        json={"application_id": app_id, "dry_run": dry_run, "auto_submit": auto_submit},
    ).json()


# --- Gates ---


def test_opt_in_required_blocks_genuine_submit(client, fixture_server):
    headers, email = _auth(client, "opt")
    # deliberately NO opt-in
    url = f"{fixture_server}/ats_greenhouse_multistep.html"
    app_id = _start(client, headers, email, url, "greenhouse")
    body = _headless(client, headers, app_id, auto_submit=True)
    assert body.get("submitted") is not True
    # Should not claim genuine apply success without opt-in
    assert body.get("genuine_apply") is not True


def test_dry_run_never_submits(client, fixture_server):
    headers, email = _auth(client, "dry")
    _opt_in(client, headers)
    url = f"{fixture_server}/ats_greenhouse_multistep.html"
    app_id = _start(client, headers, email, url, "greenhouse")
    body = _headless(client, headers, app_id, auto_submit=True, dry_run=True)
    assert body.get("status") == "filled" or body.get("ok") is True
    assert body.get("submitted") is not True


# --- ATS matrix ---


@pytest.mark.parametrize(
    "fixture,source",
    [
        ("ats_greenhouse_multistep.html", "greenhouse"),
        ("ats_workday_apply.html", "workday"),
        ("ats_ashby_apply.html", "ashby"),
        ("ats_lever_apply.html", "lever"),
        ("ats_workable_apply.html", "workable"),
        ("ats_indeed_apply.html", "indeed"),
        ("ats_smartrecruiters_apply.html", "smartrecruiters"),
        ("ats_icims_apply.html", "icims"),
    ],
)
def test_ats_fixture_genuine_submit(client, fixture_server, fixture, source):
    headers, email = _auth(client, source[:3])
    _opt_in(client, headers)
    url = f"{fixture_server}/{fixture}"
    app_id = _start(client, headers, email, url, source)
    body = _headless(client, headers, app_id, auto_submit=True)
    assert body.get("ok") is True, body
    assert body.get("submitted") is True, body
    # Indeed apply form has input[name=email] — must NOT false-positive as login wall
    assert body.get("blocked_reason") != "login_required"


def test_fill_only_sets_needs_user(client, fixture_server):
    headers, email = _auth(client, "fill")
    _opt_in(client, headers)
    url = f"{fixture_server}/ats_lever_apply.html"
    app_id = _start(client, headers, email, url, "lever")
    body = _headless(client, headers, app_id, auto_submit=False)
    assert body.get("submitted") is not True
    assert body.get("needs_user") is True or body.get("status") in ("needs_user", "filled")


# --- Confirmation honesty ---


@pytest.mark.asyncio
async def test_weak_applied_word_is_not_confirmation():
    """Body containing 'applied' alone must NOT confirm submission."""

    class FakePage:
        url = "https://www.linkedin.com/jobs/view/1/"

        async def inner_text(self, _sel):
            return (
                "Easy Apply to Acme. People who applied also viewed. "
                "Review before you apply. Applied candidates are reviewed."
            )

        async def locator(self, _sel):
            class L:
                async def count(self):
                    return 1

            return L()

    result = await detect_submission_success(FakePage())
    assert result.get("confirmed") is False


@pytest.mark.asyncio
async def test_strong_thank_you_is_confirmation():
    class FakePage:
        url = "https://boards.greenhouse.io/x/jobs/1/confirmation"

        async def inner_text(self, _sel):
            return "Thank you for applying. We've received your application."

        async def locator(self, _sel):
            class L:
                async def count(self):
                    return 0

            return L()

    result = await detect_submission_success(FakePage())
    assert result.get("confirmed") is True


# --- Quota soft-blocks ---


def test_login_required_does_not_burn_quota(client):
    headers, email = _auth(client, "quota")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        # Seed 4 login_required needs_user runs — must not exhaust free daily=5
        for i in range(4):
            db.add(
                ApplyRun(
                    user_id=user.id,
                    application_id=None,
                    job_id=None,
                    mode="headless",
                    ats_type="linkedin",
                    status="needs_user",
                    meta_json=json.dumps(
                        {"blocked_reason": "login_required", "connect_hint": "Connect LinkedIn"}
                    ),
                )
            )
        db.commit()
        q = check_apply_quota(db, user.id, requested=1, user=user)
        assert q["allowed"] is True, q
    finally:
        db.close()


def test_submitted_runs_do_burn_quota(client):
    headers, email = _auth(client, "burn")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        for i in range(5):
            db.add(
                ApplyRun(
                    user_id=user.id,
                    mode="headless",
                    ats_type="greenhouse",
                    status="submitted",
                    meta_json="{}",
                )
            )
        db.commit()
        q = check_apply_quota(db, user.id, requested=1, user=user)
        assert q["allowed"] is False, q
    finally:
        db.close()


# --- Batch meta / reconnect ---


def test_batch_status_includes_meta_and_reconnect(client, fixture_server):
    headers, email = _auth(client, "batch")
    _opt_in(client, headers)
    url = f"{fixture_server}/ats_lever_apply.html"
    app_id = _start(client, headers, email, url, "lever")

    # Create a batch-linked needs_user run with connect hint (simulate LI wall)
    batch_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        db.add(
            ApplyRun(
                user_id=user.id,
                application_id=app_id,
                mode="headless",
                ats_type="linkedin",
                status="needs_user",
                error="login_required",
                meta_json=json.dumps(
                    {
                        "batch_id": batch_id,
                        "blocked_reason": "login_required",
                        "connect_hint": "Connect LinkedIn",
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
    assert data["total"] >= 1
    assert data.get("needs_reconnect", 0) >= 1
    run = data["runs"][0]
    assert "meta" in run
    assert run["meta"].get("blocked_reason") == "login_required"
    assert run["meta"].get("connect_hint")


# --- Live LinkedIn host without Connect ---


def test_live_linkedin_without_session_returns_connect_hint(client):
    headers, email = _auth(client, "li")
    _opt_in(client, headers)
    # Real host URL — must NOT launch without BoardSession
    url = "https://www.linkedin.com/jobs/view/1234567890/"
    app_id = _start(client, headers, email, url, "linkedin")
    body = _headless(client, headers, app_id, auto_submit=True)
    assert body.get("submitted") is not True
    assert body.get("status") == "needs_user" or body.get("needs_user") is True
    assert (
        body.get("blocked_reason") == "login_required"
        or "login" in (body.get("error") or "").lower()
        or body.get("connect_hint")
    )


def test_live_indeed_without_session_returns_connect_hint(client):
    headers, email = _auth(client, "ind")
    _opt_in(client, headers)
    url = "https://www.indeed.com/viewjob?jk=abcdef123456"
    app_id = _start(client, headers, email, url, "indeed")
    body = _headless(client, headers, app_id, auto_submit=True)
    assert body.get("submitted") is not True
    assert body.get("needs_user") is True or body.get("status") == "needs_user"


# --- Indeed login wall (strong signals only) ---


def test_indeed_login_wall_fixture_needs_user(client, fixture_server):
    headers, email = _auth(client, "ilw")
    _opt_in(client, headers)
    url = f"{fixture_server}/ats_indeed_login_wall.html"
    app_id = _start(client, headers, email, url, "indeed")
    body = _headless(client, headers, app_id, auto_submit=True)
    assert body.get("submitted") is not True
    assert body.get("needs_user") is True or body.get("status") == "needs_user"
    assert body.get("blocked_reason") == "login_required", body
    assert body.get("connect_hint") or "login" in (body.get("error") or "").lower()


# --- Stale session invalidation ---


def test_login_wall_invalidates_board_session(client, fixture_server):
    """Expired Connect cookies that still hit a login wall must mark session invalid."""
    headers, email = _auth(client, "inv")
    _opt_in(client, headers)

    # Seed a "connected" LinkedIn session (raw storage_state path)
    put = client.put(
        "/api/v1/apply-engine/board-sessions/linkedin",
        headers=headers,
        json={
            "storage_state": {
                "cookies": [
                    {
                        "name": "li_at",
                        "value": "fake-expired-token",
                        "domain": ".linkedin.com",
                        "path": "/",
                        "expires": -1,
                        "httpOnly": True,
                        "secure": True,
                        "sameSite": "Lax",
                    }
                ],
                "origins": [],
            },
            "label": "stale-test",
        },
    )
    assert put.status_code == 200, put.text

    url = f"{fixture_server}/ats_linkedin_login_wall.html"
    app_id = _start(client, headers, email, url, "linkedin")
    body = _headless(client, headers, app_id, auto_submit=True)
    assert body.get("submitted") is not True
    assert body.get("status") == "needs_user" or body.get("needs_user") is True
    assert body.get("blocked_reason") == "login_required", body
    # Session must no longer be valid for Easy Apply
    listed = client.get("/api/v1/apply-engine/board-sessions", headers=headers)
    assert listed.status_code == 200
    li = next((s for s in listed.json()["sessions"] if s["board"] == "linkedin"), None)
    assert li is not None
    assert li.get("is_valid") in (False, 0)

    # get_board_session filters is_valid=1 → 404
    g = client.get("/api/v1/apply-engine/board-sessions/linkedin", headers=headers)
    assert g.status_code == 404


# --- Progress heartbeat / stale sweeper ---


def test_stale_sweeper_spares_runs_with_recent_progress(client):
    from datetime import datetime, timedelta

    from app.tasks.headless_apply_tasks import fail_stale_apply_runs

    headers, email = _auth(client, "hb")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        alive = ApplyRun(
            user_id=user.id,
            mode="headless",
            status="running",
            started_at=datetime.utcnow() - timedelta(minutes=45),
            meta_json=json.dumps(
                {
                    "last_progress_at": datetime.utcnow().isoformat() + "Z",
                    "last_step": "navigated",
                }
            ),
        )
        dead = ApplyRun(
            user_id=user.id,
            mode="headless",
            status="running",
            started_at=datetime.utcnow() - timedelta(minutes=45),
            meta_json=json.dumps(
                {
                    "last_progress_at": (
                        datetime.utcnow() - timedelta(minutes=40)
                    ).isoformat()
                    + "Z",
                    "last_step": "browser_ready",
                }
            ),
        )
        db.add(alive)
        db.add(dead)
        db.commit()
        alive_id, dead_id = alive.id, dead.id
    finally:
        db.close()

    out = fail_stale_apply_runs(max_age_minutes=30)
    assert out.get("ok") is True
    assert out.get("marked_stale", 0) >= 1

    db = SessionLocal()
    try:
        a = db.query(ApplyRun).filter(ApplyRun.id == alive_id).first()
        d = db.query(ApplyRun).filter(ApplyRun.id == dead_id).first()
        assert a.status == "running", "recent heartbeat must spare the run"
        assert d.status == "stale"
    finally:
        db.close()
