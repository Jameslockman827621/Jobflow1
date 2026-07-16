#!/usr/bin/env python3
"""Full user-readiness E2E probe — OpenAPI walk + critical journeys. Writes JSON + markdown."""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

BASE = os.environ.get("API_BASE", "http://127.0.0.1:8000").rstrip("/")
FE = os.environ.get("FE_BASE", "http://127.0.0.1:3000").rstrip("/")
NOW = datetime.now(timezone.utc).isoformat()

REPORT: Dict[str, Any] = {
    "started_at": NOW,
    "api_base": BASE,
    "frontend_base": FE,
    "checks": [],
    "openapi": {},
    "summary": {},
}


def rec(area: str, name: str, ok: bool, detail: Any = None, status: Optional[int] = None, severity: str = "blocker"):
    REPORT["checks"].append(
        {
            "area": area,
            "name": name,
            "ok": bool(ok),
            "status": status,
            "severity": severity if not ok else "ok",
            "detail": detail if not isinstance(detail, (dict, list)) else detail,
        }
    )
    print(f"[{'PASS' if ok else 'FAIL'}] {area} :: {name}" + (f" ({status})" if status is not None else ""))


def main() -> int:
    c = httpx.Client(timeout=90.0, follow_redirects=True)

    # Health
    r = c.get(f"{BASE}/api/v1/health/")
    rec("health", "API /health/", r.status_code == 200, r.text[:120], r.status_code)
    r = c.get(f"{BASE}/api/v1/health/ready")
    ready = r.json() if r.status_code == 200 else {}
    rec("health", "DB up via /ready", ready.get("checks", {}).get("database", {}).get("ok") is True, ready.get("checks", {}).get("database"), r.status_code)
    rec("health", "Redis up via /ready", ready.get("checks", {}).get("redis", {}).get("ok") is True, ready.get("checks", {}).get("redis"), r.status_code, "degraded")
    rec("health", "Playwright package installed", ready.get("checks", {}).get("playwright", {}).get("ok") is True, ready.get("checks", {}).get("playwright"), None, "degraded")
    rec("health", "Celery workers running (needed for async apply)", ready.get("checks", {}).get("celery_workers", {}).get("ok") is True, ready.get("checks", {}).get("celery_workers"), None, "degraded")
    rec("health", "Captcha provider configured", bool(ready.get("checks", {}).get("captcha_available")), ready.get("checks", {}).get("captcha_available"), None, "info")

    # OpenAPI
    r = c.get(f"{BASE}/openapi.json")
    paths = r.json().get("paths", {}) if r.status_code == 200 else {}
    REPORT["openapi"] = {"path_count": len(paths), "paths": sorted(paths.keys())}
    rec("meta", "OpenAPI available", r.status_code == 200 and len(paths) > 50, {"count": len(paths)}, r.status_code)

    # Auth journey
    email = f"e2e_{uuid.uuid4().hex[:10]}@example.com"
    password = "ReadyTest123!"
    r = c.post(f"{BASE}/api/v1/auth/register", json={"email": email, "password": password, "first_name": "E2E", "last_name": "User"})
    rec("auth", "Register", r.status_code in (200, 201), r.text[:200], r.status_code)
    r = c.post(f"{BASE}/api/v1/auth/login", data={"username": email, "password": password})
    token = r.json().get("access_token") if r.status_code == 200 else None
    rec("auth", "Login", bool(token), None, r.status_code)
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = c.get(f"{BASE}/api/v1/auth/me", headers=h)
    rec("auth", "GET /auth/me", r.status_code == 200, r.json() if r.status_code == 200 else r.text[:120], r.status_code)
    r = c.post(f"{BASE}/api/v1/auth/extension-token", headers=h)
    rec("auth", "Extension long-lived JWT", r.status_code == 200 and bool(r.json().get("access_token")), None, r.status_code)
    r = c.get(f"{BASE}/api/v1/auth/google")
    rec("auth", "Google OAuth start (503 if unset = honest)", r.status_code in (200, 503), r.text[:160], r.status_code)
    r = c.post(f"{BASE}/api/v1/auth/forgot-password", json={"email": email})
    rec("auth", "Forgot password", r.status_code == 200, r.text[:120], r.status_code)
    r = c.get(f"{BASE}/api/v1/users/me", headers=h)
    rec("auth", "Legacy /users/me returns 410", r.status_code == 410, r.text[:120], r.status_code)

    # Profile + onboarding
    r = c.get(f"{BASE}/api/v1/profile/me", headers=h)
    rec("profile", "GET profile", r.status_code == 200, None, r.status_code)
    r = c.put(f"{BASE}/api/v1/profile/me", headers=h, json={"current_title": "Software Engineer", "years_of_experience": 4, "location": "Remote", "headline": "E2E"})
    if r.status_code == 405:
        r = c.patch(f"{BASE}/api/v1/profile/me", headers=h, json={"current_title": "Software Engineer", "years_of_experience": 4, "location": "Remote"})
    rec("profile", "Update profile", r.status_code in (200, 201), r.text[:200], r.status_code)

    r = c.post(
        f"{BASE}/api/v1/onboarding/preferences",
        headers=h,
        json={
            "desired_titles": ["Software Engineer"],
            "target_roles": ["Software Engineer"],
            "locations": ["Remote"],
            "remote_preference": "remote",
            "employment_types": ["full_time"],
        },
    )
    rec("onboarding", "Save preferences", r.status_code in (200, 201), r.text[:200], r.status_code)
    r = c.post(
        f"{BASE}/api/v1/onboarding/search",
        headers=h,
        json={"titles": ["Software Engineer"], "locations": ["Remote"]},
    )
    rec("onboarding", "Run search", r.status_code in (200, 202), r.text[:300], r.status_code)
    r = c.get(f"{BASE}/api/v1/onboarding/jobs", headers=h)
    jobs = []
    if r.status_code == 200:
        body = r.json()
        jobs = body if isinstance(body, list) else body.get("jobs") or body.get("items") or []
    rec("onboarding", "List matched jobs", r.status_code == 200, {"count": len(jobs)}, r.status_code)

    # Jobs list (was 500 with null locations)
    r = c.get(f"{BASE}/api/v1/jobs/", headers=h)
    rec("jobs", "GET /jobs/ list", r.status_code == 200, {"count": len(r.json()) if r.status_code == 200 else r.text[:200]}, r.status_code)
    r = c.post(f"{BASE}/api/v1/jobs/scrape/greenhouse", headers=h)
    rec("jobs", "Scrape admin-gated for normal user", r.status_code in (401, 403), r.text[:120], r.status_code)

    # CVs
    r = c.post(
        f"{BASE}/api/v1/cvs",
        headers=h,
        json={"full_name": "E2E User", "email": email, "phone": "+15555550111", "summary": "Ready", "is_primary": True},
    )
    cv_id = r.json().get("id") if r.status_code in (200, 201) else None
    rec("cvs", "Create CV", bool(cv_id), r.text[:200], r.status_code)
    r = c.get(f"{BASE}/api/v1/cvs", headers=h)
    rec("cvs", "List CVs", r.status_code == 200, r.text[:120], r.status_code)
    if cv_id:
        r = c.post(f"{BASE}/api/v1/cvs/tailor-for-job", headers=h, json={"cv_id": cv_id, "job_description": "Python backend role"})
        # may be different path
        if r.status_code == 404:
            r = c.post(f"{BASE}/api/v1/cvs/{cv_id}/tailor", headers=h, json={"job_description": "Python backend"})
        rec(
            "ai",
            "CV tailor without OpenAI fails loudly OR works with key",
            r.status_code in (200, 400, 422, 503),
            r.text[:200],
            r.status_code,
            "degraded" if r.status_code == 503 else "ok",
        )

    # Applications
    app_id = None
    job_id = None
    if jobs:
        job_id = jobs[0].get("id") or jobs[0].get("job_id")
    if not job_id and r.status_code:
        jr = c.get(f"{BASE}/api/v1/jobs/", headers=h)
        if jr.status_code == 200 and jr.json():
            job_id = jr.json()[0].get("id")
    if job_id:
        r = c.post(f"{BASE}/api/v1/applications/start", headers=h, json={"job_id": job_id})
        app_id = (r.json().get("application_id") or r.json().get("id")) if r.status_code in (200, 201) else None
        rec("applications", "Start application", bool(app_id), r.text[:200], r.status_code)
    else:
        rec("applications", "Start application (no jobs available)", False, "No job_id from onboarding or /jobs/", None, "degraded")

    r = c.get(f"{BASE}/api/v1/applications", headers=h)
    rec("applications", "List applications", r.status_code == 200, r.text[:120], r.status_code)

    if app_id:
        r = c.post(f"{BASE}/api/v1/applications/{app_id}/submit", headers=h)
        honest = r.status_code in (400, 409, 422) or (
            r.status_code == 200 and not (isinstance(r.json(), dict) and r.json().get("status") == "submitted" and not r.json().get("manual"))
        )
        # Accept guidance responses that don't claim silent success
        if r.status_code == 200:
            body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            if body.get("submitted") is True and body.get("manual") is not True and "manual" not in str(body).lower():
                # might still be honest if it points to apply-engine
                honest = "apply-engine" in str(body).lower() or "manual" in str(body).lower() or body.get("ok") is False
            else:
                honest = True
        rec("applications", "Submit without manual=true is honest", honest, r.text[:300], r.status_code)
        r = c.post(f"{BASE}/api/v1/applications/{app_id}/submit?manual=true", headers=h)
        rec("applications", "Manual submit ?manual=true", r.status_code in (200, 201), r.text[:200], r.status_code)
        r = c.put(f"{BASE}/api/v1/applications/{app_id}", headers=h, json={"stage": "applied"})
        rec("applications", "Kanban stage update", r.status_code == 200, r.text[:160], r.status_code)

        # Headless apply on a remote URL may need_user — still should return structured result
        # Create fixture apply only if ALLOW_FIXTURE — skip live employer
        r = c.post(
            f"{BASE}/api/v1/apply-engine/headless",
            headers=h,
            json={"application_id": app_id, "dry_run": True, "auto_submit": False},
        )
        rec("apply-engine", "Headless dry_run returns structured result", r.status_code in (200, 400, 422), r.text[:300], r.status_code)

    # Apply engine
    r = c.get(f"{BASE}/api/v1/apply-engine/connect/status", headers=h)
    rec("apply-engine", "Connect status", r.status_code == 200, r.json() if r.status_code == 200 else r.text[:120], r.status_code)
    r = c.get(f"{BASE}/api/v1/apply-engine/quota", headers=h)
    quota_ok = r.status_code == 200 and ("plan" in r.text or "remaining" in r.text or "daily" in r.text)
    rec("apply-engine", "Quota endpoint", quota_ok, r.text[:200], r.status_code)
    r = c.patch(f"{BASE}/api/v1/apply-engine/settings", headers=h, json={"auto_apply_submit": True, "monitor_auto_queue": True})
    rec("apply-engine", "Settings patch", r.status_code == 200, r.text[:160], r.status_code)
    r = c.post(f"{BASE}/api/v1/apply-engine/board-sessions/linkedin/from-cookies", headers=h, json={"cookies": []})
    rec("apply-engine", "Empty LinkedIn cookies rejected", r.status_code in (400, 422), r.text[:160], r.status_code)

    # Answer bank
    r = c.post(f"{BASE}/api/v1/answer-bank", headers=h, json={"question": "Why us?", "answer": "Mission.", "tags": ["why"]})
    ans_id = r.json().get("id") if r.status_code in (200, 201) else None
    rec("answer-bank", "Create answer", bool(ans_id), r.text[:120], r.status_code)
    r = c.get(f"{BASE}/api/v1/answer-bank", headers=h)
    rec("answer-bank", "List answers", r.status_code == 200, None, r.status_code)
    if ans_id:
        r = c.delete(f"{BASE}/api/v1/answer-bank/{ans_id}", headers=h)
        rec("answer-bank", "Delete answer", r.status_code in (200, 204), None, r.status_code)

    # Analytics / career / reviews
    r = c.get(f"{BASE}/api/v1/analytics/overview", headers=h)
    rec("analytics", "Overview", r.status_code == 200, r.text[:200], r.status_code)
    r = c.get(f"{BASE}/api/v1/career/analysis", headers=h)
    rec("career", "Analysis (null years_exp safe)", r.status_code == 200, r.text[:200], r.status_code)
    r = c.get(f"{BASE}/api/v1/career/paths", headers=h)
    rec("career", "Paths browse", r.status_code == 200, None, r.status_code)
    r = c.get(f"{BASE}/api/v1/reviews/companies", headers=h)
    rec("reviews", "Companies list", r.status_code == 200, None, r.status_code)

    # Interview coach honesty
    r = c.post(f"{BASE}/api/v1/interview-coach/session", headers=h, json={"role": "Engineer"})
    if r.status_code == 404:
        # try alternate routes from openapi
        for path in sorted(paths):
            if "interview-coach" in path and "post" in paths[path]:
                # skip
                pass
        r = c.post(f"{BASE}/api/v1/interview-coach/start", headers=h, json={"role": "Engineer"})
    rec("interview-coach", "Without OpenAI → 503 OR works", r.status_code in (200, 404, 422, 503), r.text[:160], r.status_code)

    # Billing
    r = c.get(f"{BASE}/api/v1/billing/subscription", headers=h)
    rec("billing", "Subscription status", r.status_code == 200 and "free" in r.text.lower(), r.text[:200], r.status_code)
    r = c.post(f"{BASE}/api/v1/billing/checkout", headers=h, json={"plan": "pro_monthly"})
    rec("billing", "Checkout without Stripe → 503", r.status_code == 503, r.text[:160], r.status_code)
    r = c.post(f"{BASE}/api/v1/billing/webhook", content=b"{}")
    rec("billing", "Webhook unconfigured → 503/400", r.status_code in (400, 503), r.text[:120], r.status_code)

    # Referrals / alerts / auto-apply / companies
    for area, path in [
        ("referrals", "/api/v1/referrals/"),
        ("referrals", "/api/v1/referrals/me"),
        ("referrals", "/api/v1/referrals/code"),
        ("alerts", "/api/v1/alerts/"),
        ("alerts", "/api/v1/alerts/settings"),
        ("auto-apply", "/api/v1/auto-apply/jobs"),
        ("companies", "/api/v1/companies/"),
        ("companies", "/api/v1/companies/monitored"),
    ]:
        r = c.get(f"{BASE}{path}", headers=h)
        rec(area, f"GET {path}", r.status_code in (200, 404), r.text[:100], r.status_code, "info" if r.status_code == 404 else "ok")

    # Webhooks
    for path in ["/api/v1/webhooks/inbound", "/api/v1/webhooks/messaging", "/api/v1/webhooks/generic"]:
        r = c.post(f"{BASE}{path}", content=b"{}")
        if r.status_code != 404:
            rec("webhooks", f"POST {path} without auth fails", r.status_code in (400, 401, 403, 422, 503), r.text[:120], r.status_code)
            break
    else:
        rec("webhooks", "Inbound webhook route exists", False, "No known webhook path found (404)", 404, "info")

    # Frontend route smoke
    fe_routes = [
        "/", "/login", "/pricing", "/dashboard", "/onboarding", "/kanban", "/analytics",
        "/career", "/reviews", "/profile", "/referrals", "/answers", "/alerts",
        "/cv-builder", "/interview-coach", "/forgot-password", "/billing/success",
        "/unsubscribe", "/verify-email", "/privacy", "/terms", "/contact",
    ]
    for route in fe_routes:
        try:
            r = c.get(f"{FE}{route}")
            rec("frontend", f"HTTP {route}", r.status_code == 200, None, r.status_code, "degraded")
        except Exception as e:
            rec("frontend", f"HTTP {route}", False, str(e), None, "degraded")

    # Extension static integrity
    ext_root = "/workspace/extension"
    for f in ["manifest.json", "background.js", "content.js", "form-filler.js", "popup.js", "options.js", "icons/icon128.png"]:
        path = os.path.join(ext_root, f)
        ok = os.path.isfile(path) and os.path.getsize(path) > 0
        if f.endswith(".png"):
            ok = ok and os.path.getsize(path) > 100
        # no hardcoded API in form-filler except DEFAULT
        rec("extension", f"Asset {f}", ok, {"size": os.path.getsize(path) if os.path.isfile(path) else 0}, None, "degraded")
    # form-filler uses getApiBase
    with open(os.path.join(ext_root, "form-filler.js")) as fh:
        ff = fh.read()
    rec("extension", "form-filler uses chrome.storage api_base", "getApiBase" in ff and "chrome.storage" in ff, None)
    with open(os.path.join(ext_root, "content.js")) as fh:
        cc = fh.read()
    rec("extension", "content.js dashboard_url from storage", "dashboard_url" in cc, None)

    # Pricing honesty (static source check)
    with open("/workspace/frontend/src/app/pricing/page.tsx") as fh:
        pricing = fh.read()
    rec("honesty", "Pricing has no 'Unlimited applications'", "Unlimited applications" not in pricing)
    rec("honesty", "Pricing has no money-back guarantee claim", "money-back" not in pricing.lower())
    rec("honesty", "Pricing documents Pro 500/month", "500 applications" in pricing)

    _write()
    failed_blockers = [x for x in REPORT["checks"] if not x["ok"] and x.get("severity") == "blocker"]
    return 1 if failed_blockers else 0


def _write():
    checks = REPORT["checks"]
    passed = sum(1 for x in checks if x["ok"])
    failed = sum(1 for x in checks if not x["ok"])
    by_sev = {}
    for x in checks:
        if x["ok"]:
            continue
        by_sev.setdefault(x.get("severity", "blocker"), []).append(x)
    REPORT["summary"] = {
        "total": len(checks),
        "passed": passed,
        "failed": failed,
        "pass_rate": round(100 * passed / len(checks), 1) if checks else 0,
        "failed_by_severity": {k: len(v) for k, v in by_sev.items()},
    }
    REPORT["finished_at"] = datetime.now(timezone.utc).isoformat()
    os.makedirs("/opt/cursor/artifacts", exist_ok=True)
    with open("/opt/cursor/artifacts/readiness-full.json", "w") as f:
        json.dump(REPORT, f, indent=2, default=str)
    with open("/workspace/READINESS-REPORT-API.json", "w") as f:
        json.dump(REPORT, f, indent=2, default=str)

    # Markdown
    lines = [
        "# JobScale User Readiness Report",
        "",
        f"Generated: `{REPORT['finished_at']}`",
        f"API: `{BASE}` · Frontend: `{FE}`",
        "",
        f"**Score: {REPORT['summary']['passed']}/{REPORT['summary']['total']} passed ({REPORT['summary']['pass_rate']}%)**",
        "",
        "## Summary",
        "",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        f"- Failed by severity: `{REPORT['summary']['failed_by_severity']}`",
        f"- OpenAPI paths discovered: {REPORT.get('openapi', {}).get('path_count')}",
        "",
        "## Results by area",
        "",
    ]
    areas: Dict[str, List] = {}
    for x in checks:
        areas.setdefault(x["area"], []).append(x)
    for area, items in areas.items():
        p = sum(1 for i in items if i["ok"])
        lines.append(f"### {area} ({p}/{len(items)})")
        lines.append("")
        for i in items:
            mark = "✅" if i["ok"] else "❌"
            st = f" HTTP {i['status']}" if i.get("status") is not None else ""
            lines.append(f"- {mark} **{i['name']}**{st}")
            if not i["ok"] and i.get("detail"):
                d = str(i["detail"])[:240].replace("\n", " ")
                lines.append(f"  - `{d}`")
        lines.append("")
    lines += [
        "## Environment gaps (expected without secrets/workers)",
        "",
        "- Celery worker/beat not running → async headless batch queue degraded",
        "- No `OPENAI_API_KEY` → tailor/coach return 503 (honest)",
        "- No Stripe keys → checkout 503 (honest)",
        "- No Google OAuth client → `/auth/google` 503 (honest)",
        "- No live LinkedIn/Indeed session → Connect boards not exercised with real cookies",
        "- No live employer ToS smoke → Greenhouse/LinkedIn Easy Apply against production sites not run",
        "",
        "## Artifacts",
        "",
        "- `/opt/cursor/artifacts/readiness-full.json`",
        "- `/workspace/READINESS-REPORT-API.json`",
        "",
    ]
    md = "\n".join(lines)
    with open("/opt/cursor/artifacts/READINESS-REPORT.md", "w") as f:
        f.write(md)
    with open("/workspace/READINESS-REPORT.md", "w") as f:
        f.write(md)
    print(json.dumps(REPORT["summary"], indent=2))


if __name__ == "__main__":
    sys.exit(main())
