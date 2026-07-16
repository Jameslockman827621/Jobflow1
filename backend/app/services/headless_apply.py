"""
Server-side (headless) apply worker using Playwright + per-ATS adapters.

Default: fill forms and stop before submit (needs_user) unless auto_submit=True
and CAPTCHA is solved / absent.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.application import Application
from app.models.company import ApplyRun
from app.models.job import Job
from app.models.user import User
from app.services.apply_engine import build_apply_package, detect_ats
from app.services.ats_adapters import get_adapter
from app.services.proxy_pool import fingerprint_headers, playwright_proxy

logger = logging.getLogger(__name__)


async def run_headless_apply(
    db: Session,
    user: User,
    application_id: int,
    auto_submit: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    application = (
        db.query(Application)
        .filter(Application.id == application_id, Application.user_id == user.id)
        .first()
    )
    if not application:
        return {"ok": False, "error": "application_not_found"}

    job = db.query(Job).filter(Job.id == application.job_id).first()
    if not job or not job.external_url:
        return {"ok": False, "error": "job_not_found"}

    package = build_apply_package(db, user, job, application)
    applicant = dict(package["applicant"])
    ats = package.get("ats") or detect_ats(job.external_url or "")

    run = ApplyRun(
        user_id=user.id,
        application_id=application.id,
        job_id=job.id,
        mode="headless",
        ats_type=ats,
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    if dry_run:
        adapter = get_adapter(ats)
        run.status = "filled"
        run.fields_filled = len(package.get("fill_plan", {}).get("fields", []))
        run.steps_completed = 1
        run.finished_at = datetime.utcnow()
        run.meta_json = json.dumps(
            {
                "dry_run": True,
                "package_ats": ats,
                "adapter": adapter.name,
                "max_steps": adapter.max_steps,
            }
        )
        application.status = "ready_to_apply"
        application.applied_via = "headless"
        db.commit()
        return {
            "ok": True,
            "dry_run": True,
            "apply_run_id": run.id,
            "ats": ats,
            "fields_planned": run.fields_filled,
            "adapter": adapter.name,
            "package": package,
        }

    if not getattr(settings, "HEADLESS_APPLY_ENABLED", True):
        run.status = "queued"
        run.finished_at = datetime.utcnow()
        run.meta_json = json.dumps({"disabled": True})
        db.commit()
        return {"ok": False, "error": "headless_disabled", "apply_run_id": run.id}

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        run.status = "failed"
        run.error = "playwright_not_installed"
        run.finished_at = datetime.utcnow()
        db.commit()
        return {"ok": False, "error": "playwright_not_installed", "apply_run_id": run.id}

    try:
        proxy = playwright_proxy()
        headers = fingerprint_headers()
        adapter = get_adapter(ats)
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                proxy=proxy,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(
                user_agent=headers.get("User-Agent"),
                locale="en-US",
                extra_http_headers={k: v for k, v in headers.items() if k != "User-Agent"},
            )
            page = await context.new_page()
            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )
            await page.goto(job.external_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(1200)

            result = await adapter.fill(
                page,
                applicant,
                auto_submit=auto_submit and getattr(settings, "HEADLESS_APPLY_AUTO_SUBMIT", False),
            )
            await browser.close()

        if result.submitted:
            status = "submitted"
            application.status = "submitted"
            application.stage = "applied"
            application.submitted_at = datetime.utcnow()
            application.applied_via = "headless"
        elif result.captcha_present and not result.captcha_solved:
            status = "captcha"
            application.status = "in_progress"
            application.applied_via = "headless"
        elif result.needs_user:
            status = "needs_user"
            application.status = "in_progress"
            application.applied_via = "headless"
        else:
            status = "filled"
            application.status = "in_progress"
            application.applied_via = "headless"

        run.status = status
        run.fields_filled = result.fields_filled
        run.steps_completed = result.steps_completed
        run.captcha_solved = result.captcha_solved
        run.finished_at = datetime.utcnow()
        run.meta_json = json.dumps(result.to_dict())
        if result.errors:
            run.error = "; ".join(result.errors)[:2000]
        db.commit()

        return {
            "ok": True,
            "apply_run_id": run.id,
            "status": status,
            "fields_filled": result.fields_filled,
            "fields_attempted": result.fields_attempted,
            "steps_completed": result.steps_completed,
            "captcha_present": result.captcha_present,
            "captcha_solved": result.captcha_solved,
            "submitted": result.submitted,
            "needs_user": result.needs_user,
            "filled_keys": result.filled_keys,
            "ats": ats,
            "adapter": adapter.name,
            "core_ok": (result.meta or {}).get("core_ok"),
            "page_url": result.page_url,
        }
    except Exception as exc:
        logger.exception("Headless apply failed")
        run.status = "failed"
        run.error = str(exc)[:2000]
        run.finished_at = datetime.utcnow()
        db.commit()
        return {"ok": False, "error": str(exc), "apply_run_id": run.id}


async def live_fill_url(
    url: str,
    applicant: Dict[str, Any],
    *,
    ats: str | None = None,
    auto_submit: bool = False,
) -> Dict[str, Any]:
    """Direct live fill against a URL (used by integration tests / ops). Never submits unless asked."""
    from playwright.async_api import async_playwright

    ats = ats or detect_ats(url)
    adapter = get_adapter(ats)
    headers = fingerprint_headers()
    proxy = playwright_proxy()
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy=proxy,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent=headers.get("User-Agent"),
            locale="en-US",
            extra_http_headers={k: v for k, v in headers.items() if k != "User-Agent"},
        )
        page = await context.new_page()
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(1500)
        result = await adapter.fill(page, applicant, auto_submit=auto_submit)
        # Read back core field values for verification
        values = await page.evaluate(
            """() => {
              const val = (sel) => {
                const el = document.querySelector(sel);
                return el ? (el.value || '') : null;
              };
              return {
                first_name: val('#first_name') || val("input[name='name']") || val("input[autocomplete='given-name']"),
                last_name: val('#last_name') || val("input[autocomplete='family-name']"),
                email: val('#email') || val("input[name='email']") || val("input[type='email']"),
                phone: val('#phone') || val("input[name='phone']") || val("input[type='tel']"),
                linkedin: val("input[name=\\"urls[LinkedIn]\\"]") || val("input[aria-label*='LinkedIn' i]"),
              };
            }"""
        )
        await browser.close()
    out = result.to_dict()
    out["verified_values"] = values
    out["ok"] = True
    return out
