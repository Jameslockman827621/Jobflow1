#!/usr/bin/env python3
"""
Scale smoke: register N users, create M jobs each, batch-start applications, print timings.

Usage (from backend/):
  python scripts/scale_apply_smoke.py
  python scripts/scale_apply_smoke.py --users 5 --jobs 20
  python scripts/scale_apply_smoke.py --base-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import sys
import time
import uuid
from pathlib import Path

# Allow `python scripts/scale_apply_smoke.py` from backend/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ensure_jobs_and_cv(email: str, job_count: int) -> list[int]:
    from app.database import SessionLocal, init_db
    from app.models.cv import CV
    from app.models.job import Job, JobSource
    from app.models.user import User

    init_db()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise RuntimeError(f"User not found after register: {email}")

        source = db.query(JobSource).filter_by(name="greenhouse").first()
        if not source:
            source = JobSource(name="greenhouse", base_url="https://boards-api.greenhouse.io")
            db.add(source)
            db.commit()
            db.refresh(source)

        if not db.query(CV).filter(CV.user_id == user.id).first():
            db.add(
                CV(
                    user_id=user.id,
                    full_name="Scale Smoke",
                    email=email,
                    phone="+15555550199",
                    linkedin_url="https://linkedin.com/in/scalesmoke",
                    skills=["Python", "FastAPI"],
                    is_primary=True,
                )
            )
            db.commit()

        job_ids: list[int] = []
        for i in range(job_count):
            job = Job(
                source_id=source.id,
                external_id=f"smoke-{uuid.uuid4().hex[:12]}",
                external_url=f"https://boards.greenhouse.io/example/jobs/{10000 + i}",
                title=f"Smoke Engineer {i}",
                company="SmokeCo",
                location="Remote",
                is_active=True,
            )
            db.add(job)
            db.flush()
            job_ids.append(job.id)
        db.commit()
        return job_ids
    finally:
        db.close()


def _http_register_login(base_url: str, email: str, password: str) -> str:
    import httpx

    r = httpx.post(
        f"{base_url}/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "Scale",
            "last_name": "Smoke",
        },
        timeout=30.0,
    )
    if r.status_code not in (200, 201, 400):
        raise RuntimeError(f"register failed {r.status_code}: {r.text[:300]}")

    login = httpx.post(
        f"{base_url}/api/v1/auth/login",
        data={"username": email, "password": password},
        timeout=30.0,
    )
    if login.status_code != 200:
        raise RuntimeError(f"login failed {login.status_code}: {login.text[:300]}")
    return login.json()["access_token"]


def _batch_start(base_url: str, token: str, job_ids: list[int], chunk: int = 50) -> tuple[int, float]:
    import httpx

    headers = {"Authorization": f"Bearer {token}"}
    created = 0
    t0 = time.perf_counter()
    for i in range(0, len(job_ids), chunk):
        part = job_ids[i : i + chunk]
        r = httpx.post(
            f"{base_url}/api/v1/applications/batch-start",
            headers=headers,
            json={"job_ids": part},
            timeout=60.0,
        )
        if r.status_code != 200:
            raise RuntimeError(f"batch-start failed {r.status_code}: {r.text[:400]}")
        created += int(r.json().get("total") or 0)
    elapsed = time.perf_counter() - t0
    return created, elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Scale apply smoke (register + batch-start)")
    parser.add_argument("--users", type=int, default=5, help="Number of users to register (default 5)")
    parser.add_argument("--jobs", type=int, default=20, help="Jobs per user to create + batch-start (default 20)")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--password", default="ScaleSmoke123!", help="Password for smoke users")
    args = parser.parse_args()

    print(f"scale_apply_smoke: users={args.users} jobs_each={args.jobs} base={args.base_url}")
    overall_t0 = time.perf_counter()
    totals = {"users": 0, "applications": 0, "batch_seconds": 0.0}

    for u in range(args.users):
        email = f"scale_smoke_{uuid.uuid4().hex[:10]}@example.com"
        user_t0 = time.perf_counter()
        token = _http_register_login(args.base_url, email, args.password)
        job_ids = _ensure_jobs_and_cv(email, args.jobs)
        created, batch_s = _batch_start(args.base_url, token, job_ids)
        user_s = time.perf_counter() - user_t0
        totals["users"] += 1
        totals["applications"] += created
        totals["batch_seconds"] += batch_s
        print(
            f"  user {u + 1}/{args.users}: {email} "
            f"apps={created} batch={batch_s:.3f}s total={user_s:.3f}s"
        )

    overall = time.perf_counter() - overall_t0
    print("---")
    print(
        f"done: users={totals['users']} applications={totals['applications']} "
        f"batch_time={totals['batch_seconds']:.3f}s wall={overall:.3f}s"
    )
    if totals["applications"]:
        print(
            f"avg batch latency/app: "
            f"{(totals['batch_seconds'] / totals['applications']) * 1000:.1f} ms"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
