"""
Live ATS fill tests against real public job boards.

These hit the network and use Playwright. They FILL but do not SUBMIT
(auto_submit=False) to avoid spamming employers.
"""

from __future__ import annotations

import os

import httpx
import pytest

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-32chars")

from app.services.headless_apply import live_fill_url


APPLICANT = {
    "first_name": "Alex",
    "last_name": "Chen",
    "full_name": "Alex Chen",
    "email": "alex.chen.jobscale.test@example.com",
    "phone": "+15555550123",
    "linkedin": "https://www.linkedin.com/in/alexchen-test",
    "portfolio": "https://github.com/alexchen-test",
    "location": "San Francisco, CA",
    "current_company": "Acme Corp",
    "current_title": "Software Engineer",
    "years_experience": 5,
    "skills": ["Python", "TypeScript", "PostgreSQL"],
    "summary": "Engineer focused on reliable systems and clear communication.",
    "work_auth": True,
    "needs_sponsorship": False,
}


def _greenhouse_job_url() -> str:
    r = httpx.get(
        "https://boards-api.greenhouse.io/v1/boards/gitlab/jobs",
        params={"content": "false"},
        timeout=30,
    )
    r.raise_for_status()
    jobs = r.json().get("jobs") or []
    assert jobs, "No GitLab Greenhouse jobs"
    url = jobs[0].get("absolute_url") or jobs[0].get("url")
    assert url
    return url


def _lever_apply_url() -> str:
    r = httpx.get("https://api.lever.co/v0/postings/wealthfront?mode=json", timeout=30)
    r.raise_for_status()
    jobs = r.json()
    assert jobs, "No Wealthfront Lever jobs"
    hosted = jobs[0].get("hostedUrl")
    assert hosted
    return hosted.rstrip("/") + "/apply"


@pytest.mark.asyncio
async def test_live_greenhouse_fill_core_fields():
    url = _greenhouse_job_url()
    result = await live_fill_url(url, APPLICANT, ats="greenhouse", auto_submit=False)
    assert result["ok"] is True
    assert result["ats"] == "greenhouse"
    assert result["fields_filled"] >= 3
    assert "first_name" in result["filled_keys"]
    assert "last_name" in result["filled_keys"]
    assert "email" in result["filled_keys"]
    assert result.get("core_ok") or result["meta"].get("core_ok")
    values = result["verified_values"]
    assert values["first_name"] == "Alex"
    assert values["last_name"] == "Chen"
    assert values["email"] == APPLICANT["email"]
    # Must not submit in this test
    assert result["submitted"] is False
    assert result["needs_user"] is True


@pytest.mark.asyncio
async def test_live_lever_fill_core_fields():
    url = _lever_apply_url()
    result = await live_fill_url(url, APPLICANT, ats="lever", auto_submit=False)
    assert result["ok"] is True
    assert result["ats"] == "lever"
    assert result["fields_filled"] >= 3
    assert "full_name" in result["filled_keys"]
    assert "email" in result["filled_keys"]
    values = result["verified_values"]
    # Lever uses name/email fields
    assert values["email"] == APPLICANT["email"]
    assert result["submitted"] is False
