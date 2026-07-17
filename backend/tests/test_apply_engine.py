"""Unit tests for apply engine, ATS detection, company directory, messaging."""

import pytest

from app.services.apply_engine import (
    build_applicant_payload,
    build_fill_plan,
    detect_ats,
    map_field_key,
    value_for_key,
)
from app.services.messaging import messaging_service
from app.services.proxy_pool import fingerprint_headers, pool_status
from app.scrapers.companies import (
    ASHBY_COMPANIES,
    GREENHOUSE_COMPANIES,
    LEVER_COMPANIES,
    WORKABLE_COMPANIES,
    all_seed_companies,
)


class DummyUser:
    def __init__(self, email="test@example.com"):
        self.email = email
        self.id = 1


class DummyProfile:
    first_name = "Alex"
    last_name = "Chen"
    location = "London, UK"
    current_title = "Software Engineer"
    current_company = "Acme"
    years_of_experience = 5.0
    min_salary = 90000
    max_salary = 120000
    resume_text = "Experienced engineer."
    skills = []


class DummyCV:
    id = 7
    full_name = "Alex Chen"
    email = "alex@example.com"
    phone = "+447700900123"
    linkedin_url = "https://linkedin.com/in/alexchen"
    portfolio_url = "https://github.com/alexchen"
    location = "London, UK"
    summary = "Builder of reliable products."
    skills = ["Python", "React", "AWS"]
    experience = []
    education = []


def test_detect_ats_variants():
    assert detect_ats("https://boards.greenhouse.io/stripe/jobs/123") == "greenhouse"
    assert detect_ats("https://jobs.lever.co/netflix/abc") == "lever"
    assert detect_ats("https://apply.workable.com/acme/") == "workable"
    assert detect_ats("https://jobs.ashbyhq.com/openai/xyz") == "ashby"
    assert detect_ats("https://nvidia.wd5.myworkdayjobs.com/en-US/job") == "workday"


def test_map_field_key():
    assert map_field_key("Email Address") == "email"
    assert map_field_key("LinkedIn Profile") == "linkedin"
    assert map_field_key("Phone Number") == "phone"
    assert map_field_key("Upload Resume") == "resume"


def test_build_applicant_and_fill_plan():
    payload = build_applicant_payload(DummyUser(), DummyProfile(), DummyCV())
    assert payload["first_name"] == "Alex"
    assert payload["phone"].startswith("+44")
    assert payload["linkedin"].startswith("https://")
    assert value_for_key(payload, "salary") == "90000-120000"

    plan = build_fill_plan(payload, "workday")
    assert plan["multi_step"] is True
    assert plan["max_steps"] >= 4
    assert "select" in plan["field_types_supported"]
    assert "checkbox" in plan["field_types_supported"]
    assert any(f["key"] == "email" for f in plan["fields"])


@pytest.mark.asyncio
async def test_open_ended_heuristic():
    from app.services.apply_engine import answer_open_ended

    payload = build_applicant_payload(DummyUser(), DummyProfile(), DummyCV())
    ans = await answer_open_ended("Why do you want to work at this company?", payload, None)
    assert "excited" in ans.lower() or "experience" in ans.lower()
    assert len(ans) > 20


def test_company_seed_scale():
    seeds = all_seed_companies()
    assert len(GREENHOUSE_COMPANIES) >= 80
    assert len(LEVER_COMPANIES) >= 40
    assert len(WORKABLE_COMPANIES) >= 20
    assert len(ASHBY_COMPANIES) >= 30
    assert len(seeds) >= 150
    ats = {s["ats_type"] for s in seeds}
    assert {"greenhouse", "lever", "workable", "ashby", "custom"} <= ats


def test_messaging_commands():
    assert messaging_service.parse_command("help")["command"] == "HELP"
    assert messaging_service.parse_command("APPLY 42")["args"] == ["42"]
    status = messaging_service.status()
    assert "whatsapp" in status and "imessage" in status


def test_proxy_fingerprint():
    headers = fingerprint_headers()
    assert "User-Agent" in headers
    assert "Sec-Ch-Ua" in headers
    st = pool_status()
    assert "enabled" in st
