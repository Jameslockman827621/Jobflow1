"""LinkedIn Easy Apply, Indeed, company-site, and ATS handoff coverage."""

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
from app.services.board_classify import classify_url
from app.services.ats_adapters import get_adapter


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
    base = f"http://127.0.0.1:{port}"
    gh = f"{base}/ats_greenhouse_apply.html"
    originals = {}
    for name in ("ats_indeed_external.html", "ats_company_site.html"):
        path = FIXTURE_DIR / name
        originals[path] = path.read_text(encoding="utf-8")
        # Always rewrite so stale ports from prior runs cannot stick
        text = originals[path]
        text = text.replace("HANDOFF_URL", gh)
        # Also rewrite any leftover absolute handoff from a previous run
        import re

        text = re.sub(
            r'href="http://127\.0\.0\.1:\d+/ats_greenhouse_apply\.html"',
            f'href="{gh}"',
            text,
        )
        path.write_text(text, encoding="utf-8")
    yield base
    httpd.shutdown()
    for path, content in originals.items():
        path.write_text(content, encoding="utf-8")


def _auth(client, prefix="bc"):
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "BoardCov123!",
            "first_name": "Blair",
            "last_name": "Cover",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "BoardCov123!"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.patch(
        "/api/v1/apply-engine/settings",
        headers=headers,
        json={"auto_apply_submit": True},
    )
    return headers, email


def _seed_job(email, url, source_name, title="Board Role"):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        src = db.query(JobSource).filter_by(name=source_name).first()
        if not src:
            src = JobSource(name=source_name, base_url=f"https://{source_name}.example")
            db.add(src)
            db.commit()
            db.refresh(src)
        job = Job(
            source_id=src.id,
            external_id=f"{source_name}-{uuid.uuid4().hex[:8]}",
            external_url=url,
            title=title,
            company="JobScaleTest",
            is_active=True,
        )
        db.add(job)
        if not db.query(CV).filter(CV.user_id == user.id).first():
            db.add(
                CV(
                    user_id=user.id,
                    full_name="Blair Cover",
                    email=email,
                    phone="+15555550888",
                    linkedin_url="https://linkedin.com/in/blaircover",
                    skills=["Python"],
                    is_primary=True,
                )
            )
        db.commit()
        db.refresh(job)
        return job.id
    finally:
        db.close()


def test_classify_url_modes():
    assert classify_url("https://www.linkedin.com/jobs/view/123")["apply_mode"] == "easy_apply"
    assert classify_url("https://www.indeed.com/viewjob?jk=abc")["board"] == "indeed"
    assert classify_url("https://boards.greenhouse.io/x/jobs/1")["apply_mode"] == "ats_direct"
    assert classify_url("https://careers.acme.com/jobs/1")["apply_mode"] == "company_site"


def test_adapters_registered():
    assert get_adapter("linkedin").name == "linkedin"
    assert get_adapter("indeed").name == "indeed"
    assert get_adapter("generic").name == "generic"


def test_linkedin_easy_apply_submit(client, fixture_server):
    headers, email = _auth(client, "li")
    url = f"{fixture_server}/ats_linkedin_easy_apply.html"
    job_id = _seed_job(email, url, "linkedin", "LI Easy Apply")
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
    assert body.get("ats") == "linkedin" or body.get("adapter") == "linkedin"


def test_linkedin_login_wall(client, fixture_server):
    headers, email = _auth(client, "lilogin")
    url = f"{fixture_server}/ats_linkedin_login_wall.html"
    job_id = _seed_job(email, url, "linkedin", "LI Login")
    app_id = client.post(
        "/api/v1/applications/start", headers=headers, json={"job_id": job_id}
    ).json()["application_id"]
    body = client.post(
        "/api/v1/apply-engine/headless",
        headers=headers,
        json={"application_id": app_id, "dry_run": False, "auto_submit": True},
    ).json()
    assert body["ok"] is True
    assert body["submitted"] is False
    assert body["status"] == "needs_user"


def test_indeed_apply_submit(client, fixture_server):
    headers, email = _auth(client, "ind")
    url = f"{fixture_server}/ats_indeed_apply.html"
    job_id = _seed_job(email, url, "indeed", "Indeed Apply")
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


def test_indeed_external_handoff_to_greenhouse(client, fixture_server):
    headers, email = _auth(client, "indh")
    url = f"{fixture_server}/ats_indeed_external.html"
    job_id = _seed_job(email, url, "indeed", "Indeed External")
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
    # Handoff meta should mention greenhouse
    # status submitted is the proof handoff filled+submitted greenhouse fixture


def test_company_site_direct_submit(client, fixture_server):
    headers, email = _auth(client, "co")
    url = f"{fixture_server}/ats_company_site_direct.html"
    job_id = _seed_job(email, url, "generic", "Company Direct")
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


def test_company_site_ats_handoff(client, fixture_server):
    headers, email = _auth(client, "coh")
    url = f"{fixture_server}/ats_company_site.html"
    job_id = _seed_job(email, url, "generic", "Company Handoff")
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


def test_board_session_api(client):
    headers, _ = _auth(client, "sess")
    r = client.put(
        "/api/v1/apply-engine/board-sessions/linkedin",
        headers=headers,
        json={
            "storage_state": {"cookies": [], "origins": []},
            "label": "test-li",
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True
    g = client.get("/api/v1/apply-engine/board-sessions/linkedin", headers=headers)
    assert g.status_code == 200
    assert g.json()["has_storage_state"] is True
    listed = client.get("/api/v1/apply-engine/board-sessions", headers=headers)
    assert any(s["board"] == "linkedin" for s in listed.json()["sessions"])
    d = client.delete("/api/v1/apply-engine/board-sessions/linkedin", headers=headers)
    assert d.status_code == 200


def test_board_classify_endpoint(client):
    headers, _ = _auth(client, "clf")
    r = client.get(
        "/api/v1/apply-engine/board-classify",
        headers=headers,
        params={"url": "https://www.linkedin.com/jobs/view/999"},
    )
    assert r.status_code == 200
    assert r.json()["board"] == "linkedin"
    assert r.json()["needs_session"] is True
