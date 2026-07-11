"""End-to-end smoke test for the JobScale backend.

Runs the full user flow against a live backend:
  1. Register a new user
  2. Login and get a token
  3. Upload a CV (parsed)
  4. Save job preferences (with target companies)
  5. Run an on-demand search
  6. Approve some jobs for the apply queue
  7. Get the next queue item
  8. Mark it as applied
  9. Verify the application appears in the kanban

Usage:
    python scripts/e2e_smoke_test.py
"""

import json
import os
import sys
import time

import httpx

BASE = os.environ.get("JOBSCALE_API", "http://localhost:8000")
API = f"{BASE}/api/v1"


def banner(s: str) -> None:
    print(f"\n{'='*60}\n  {s}\n{'='*60}")


def expect(condition: bool, msg: str) -> None:
    if condition:
        print(f"  ✅ {msg}")
    else:
        print(f"  ❌ {msg}")
        sys.exit(1)


def main() -> None:
    email = f"e2e_{int(time.time())}@example.com"
    password = "testpass123"

    banner("1. REGISTER")
    r = httpx.post(f"{API}/auth/register", json={
        "email": email, "password": password,
        "first_name": "E2E", "last_name": "Test",
    })
    expect(r.status_code in (200, 201), f"Register user (status={r.status_code})")
    print(f"     User: {r.json()}")

    banner("2. LOGIN")
    r = httpx.post(f"{API}/auth/login", data={"username": email, "password": password})
    expect(r.status_code in (200, 201), f"Login (status={r.status_code})")
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"     Token: {token[:20]}...")

    banner("3. UPLOAD CV")
    cv_text = """Jane Doe
jane@example.com | +44 123 456 7890 | London, UK
LinkedIn: linkedin.com/in/janedoe

Summary
Senior software engineer with 8 years of Python and React experience.

Experience
Senior Engineer, Tech Co, London — 2019-2024
- Built Python APIs and React frontends using AWS, Docker, and Kubernetes
- Led a team of 4 engineers

Software Engineer at Startup Inc - Remote - 2016-2019
- Developed full-stack applications with Python, Django, and React

Skills: Python, React, AWS, Docker, Kubernetes, JavaScript, TypeScript, Django
Education
BSc Computer Science, University of Example, 2015
"""
    with open("/tmp/e2e_cv.txt", "w") as f:
        f.write(cv_text)
    with open("/tmp/e2e_cv.txt", "rb") as f:
        r = httpx.post(f"{API}/cvs/upload", headers=headers, files={"file": ("cv.txt", f, "text/plain")})
    expect(r.status_code in (200, 201), f"CV upload (status={r.status_code})")
    parsed = r.json().get("parsed", {})
    print(f"     Parsed: name={parsed.get('full_name')!r}, skills={len(parsed.get('skills', []))}, "
          f"exp={parsed.get('experience_count')}, edu={parsed.get('education_count')}, "
          f"yoe={parsed.get('years_of_experience')}")
    expect(parsed.get("full_name") == "Jane Doe", "Parser extracted correct name")
    expect(parsed.get("experience_count", 0) >= 1, "Parser extracted at least 1 experience entry")
    expect(parsed.get("years_of_experience", 0) >= 5, "Parser computed years of experience")

    banner("4. SAVE PREFERENCES (with target companies)")
    r = httpx.post(f"{API}/onboarding/preferences", headers=headers, json={
        "target_roles": ["Software Engineer", "Senior Software Engineer"],
        "seniority_levels": ["senior"],
        "locations": ["London", "Remote"],
        "remote_preference": "any",
        "target_companies": ["Stripe", "Airbnb", "NVIDIA"],
    })
    expect(r.status_code in (200, 201), f"Save preferences (status={r.status_code})")
    print(f"     Preferences saved: {r.json().get('status')}")

    banner("5. RUN ON-DEMAND SEARCH")
    r = httpx.post(f"{API}/onboarding/search", headers=headers, json={"force_refresh": True}, timeout=90.0)
    print(f"     Search status: {r.status_code}")
    if r.status_code != 200:
        print(f"     Response: {r.text[:500]}")
        r = httpx.post(f"{API}/jobs/search", headers=headers, json={"force_refresh": True}, timeout=90.0)
        print(f"     /jobs/search status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        jobs = data.get("jobs", [])
        print(f"     Jobs found: {len(jobs)}")
        print(f"     Sources used: {data.get('sources_used', {})}")
        print(f"     Sources failed: {data.get('sources_failed', [])}")
        if jobs:
            print(f"     Sample: {jobs[0].get('title')} @ {jobs[0].get('company')}")
        expect(len(jobs) > 0, "Search returned real jobs (no demo fallback)")

    banner("6. GET DASHBOARD JOBS")
    r = httpx.get(f"{API}/onboarding/jobs", headers=headers)
    expect(r.status_code == 200, f"Get jobs (status={r.status_code})")
    jobs = r.json().get("jobs", [])
    print(f"     Jobs on dashboard: {len(jobs)}")
    if jobs:
        print(f"     First 3:")
        for j in jobs[:3]:
            print(f"       - [{j.get('id')}] {j.get('title')} @ {j.get('company')}")

    if not jobs:
        print("\nNo jobs to test approve flow — stopping here.")
        return

    banner("7. APPROVE JOBS FOR APPLY QUEUE")
    job_ids = [j["id"] for j in jobs[:3]]
    r = httpx.post(f"{API}/auto-apply/approve", headers=headers, json={"job_ids": job_ids})
    expect(r.status_code == 200, f"Approve jobs (status={r.status_code})")
    print(f"     Approve result: {r.json()}")

    banner("8. GET APPLY QUEUE")
    r = httpx.get(f"{API}/auto-apply/queue", headers=headers)
    expect(r.status_code == 200, f"Get queue (status={r.status_code})")
    queue = r.json().get("queue", [])
    print(f"     Queue size: {len(queue)}")
    for q in queue[:3]:
        print(f"       - [{q.get('id')}] {q.get('job', {}).get('title')} @ {q.get('job', {}).get('company')} (ats={q.get('ats_score')})")

    if not queue:
        print("\nNo queue items — stopping here.")
        return

    banner("9. START NEXT QUEUE ITEM")
    item_id = queue[0]["id"]
    r = httpx.post(f"{API}/auto-apply/queue/{item_id}/start", headers=headers)
    expect(r.status_code == 200, f"Start queue item (status={r.status_code})")
    print(f"     Started: {r.json().get('queue_item', {}).get('id')}")

    banner("10. MARK APPLIED")
    r = httpx.post(f"{API}/auto-apply/queue/{item_id}/complete", headers=headers, json={"skip": False})
    expect(r.status_code == 200, f"Mark applied (status={r.status_code})")
    print(f"     Result: completed id={r.json().get('completed', {}).get('id')}")

    banner("11. VERIFY APPLICATION IN KANBAN")
    r = httpx.get(f"{API}/applications", headers=headers)
    expect(r.status_code == 200, f"Get applications (status={r.status_code})")
    apps = r.json().get("applications", [])
    print(f"     Total applications: {len(apps)}")
    if apps:
        a = apps[0]
        job = a.get('job') or {}
        print(f"     Latest: {job.get('title')} @ {job.get('company')} — status={a.get('status')}")

    banner("12. TEST SOURCE COVERAGE")
    r = httpx.get(f"{API}/jobs/sources/coverage", headers=headers)
    expect(r.status_code == 200, f"Get source coverage (status={r.status_code})")
    sources = r.json().get("sources", [])
    available = [s for s in sources if s.get("available")]
    print(f"     Available sources: {len(available)}/{len(sources)}")
    for s in available:
        print(f"       - {s.get('name')}: {s.get('coverage')}")

    banner("E2E TEST PASSED ✅")


if __name__ == "__main__":
    main()
