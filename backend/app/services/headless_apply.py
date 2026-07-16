"""
Server-side (headless) apply worker using Playwright + per-ATS adapters.

Default: fill forms and stop before submit (needs_user) unless auto_submit=True
and CAPTCHA is solved / absent.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.application import Application
from app.models.company import ApplyRun
from app.models.cv import CV
from app.models.job import Job
from app.models.user import User
from app.services.apply_engine import build_apply_package, detect_ats
from app.services.ats_adapters import get_adapter
from app.services.proxy_pool import (
    fingerprint_headers,
    human_delay,
    playwright_proxy,
    stealth_init_script,
)
from app.services.resume_files import ensure_resume_local_path

logger = logging.getLogger(__name__)

SCREENSHOT_DIR = "/tmp/jobscale_screenshots"


async def _save_failure_screenshot(page, apply_run_id: int) -> Optional[str]:
    try:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        path = os.path.join(SCREENSHOT_DIR, f"{apply_run_id}.png")
        await page.screenshot(path=path, full_page=True)
        return path
    except Exception as exc:
        logger.warning("Screenshot failed for apply_run %s: %s", apply_run_id, exc)
        return None


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
    # Prefer URL ATS, but fall back to job source name (local fixtures / custom domains)
    ats = package.get("ats") or detect_ats(job.external_url or "")
    if ats in ("generic", "", None) and job.source is not None:
        src = (getattr(job.source, "name", None) or "").lower()
        if src in ("greenhouse", "lever", "ashby", "workday", "workable"):
            ats = src
            package["ats"] = ats

    cv = None
    if application.cv_id:
        cv = db.query(CV).filter(CV.id == application.cv_id, CV.user_id == user.id).first()
    if not cv and applicant.get("cv_id"):
        cv = db.query(CV).filter(CV.id == applicant["cv_id"], CV.user_id == user.id).first()
    if not cv:
        cv = (
            db.query(CV)
            .filter(CV.user_id == user.id)
            .order_by(CV.is_primary.desc(), CV.created_at.desc())
            .first()
        )

    ensure_resume_local_path(user.id, applicant, cv)

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
                "resume_local_path": applicant.get("resume_local_path"),
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
            "resume_local_path": applicant.get("resume_local_path"),
            "package": package,
        }

    if not getattr(settings, "HEADLESS_APPLY_ENABLED", True):
        run.status = "queued"
        run.finished_at = datetime.utcnow()
        run.meta_json = json.dumps({"disabled": True})
        db.commit()
        return {"ok": False, "error": "headless_disabled", "apply_run_id": run.id}

    # Genuine submit requires: request auto_submit + user opt-in + platform kill-switch ON
    platform_allows_submit = bool(getattr(settings, "HEADLESS_APPLY_AUTO_SUBMIT", True))
    user_allows_submit = bool(getattr(user, "auto_apply_submit", False))
    should_submit = bool(auto_submit) and platform_allows_submit and user_allows_submit

    try:
        from playwright.async_api import async_playwright  # noqa: F401
    except ImportError:
        run.status = "failed"
        run.error = "playwright_not_installed"
        run.finished_at = datetime.utcnow()
        db.commit()
        return {"ok": False, "error": "playwright_not_installed", "apply_run_id": run.id}

    from playwright.async_api import TimeoutError as PlaywrightTimeoutError
    from playwright.async_api import async_playwright

    adapter = get_adapter(ats)
    screenshot_path = None
    last_error = None
    result = None

    for attempt in range(2):  # retry once on timeout
        page = None
        browser = None
        try:
            proxy = playwright_proxy(user_id=user.id)
            headers = fingerprint_headers()
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
                await page.add_init_script(stealth_init_script)
                await human_delay(300, 900)
                await page.goto(job.external_url, wait_until="domcontentloaded", timeout=60000)
                await human_delay(800, 1600)

                result = await adapter.fill(
                    page,
                    applicant,
                    auto_submit=should_submit,
                )
                await browser.close()
                browser = None
            break  # success
        except (PlaywrightTimeoutError, TimeoutError) as exc:
            last_error = exc
            logger.warning("Headless apply timeout (attempt %s): %s", attempt + 1, exc)
            if page:
                screenshot_path = await _save_failure_screenshot(page, run.id)
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass
            if attempt == 0:
                await human_delay(500, 1200)
                continue
        except Exception as exc:
            last_error = exc
            logger.exception("Headless apply failed")
            if page:
                screenshot_path = await _save_failure_screenshot(page, run.id)
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass
            break

    if result is None:
        meta = {"error": str(last_error) if last_error else "unknown"}
        if screenshot_path:
            meta["screenshot_path"] = screenshot_path
        run.status = "failed"
        run.error = str(last_error)[:2000] if last_error else "unknown"
        run.finished_at = datetime.utcnow()
        run.meta_json = json.dumps(meta)
        db.commit()
        return {
            "ok": False,
            "error": str(last_error) if last_error else "unknown",
            "apply_run_id": run.id,
            "screenshot_path": screenshot_path,
        }

    # Captcha unsolved → needs_user (not a separate captcha status for user-facing)
    if result.submitted:
        status = "submitted"
        application.status = "submitted"
        application.stage = "applied"
        application.submitted_at = datetime.utcnow()
        application.applied_via = "headless"
    elif result.captcha_present and not result.captcha_solved:
        status = "needs_user"
        application.status = "in_progress"
        application.applied_via = "headless"
        result.needs_user = True
    elif result.needs_user:
        status = "needs_user"
        application.status = "in_progress"
        application.applied_via = "headless"
    else:
        status = "filled"
        application.status = "in_progress"
        application.applied_via = "headless"

    meta = result.to_dict()
    meta["resume_local_path"] = applicant.get("resume_local_path")
    meta["submit_policy"] = {
        "requested_auto_submit": bool(auto_submit),
        "user_auto_apply_submit": user_allows_submit,
        "platform_allows_submit": platform_allows_submit,
        "should_submit": should_submit,
    }
    if auto_submit and not should_submit:
        meta["submit_blocked_reason"] = (
            "user_opt_in_required"
            if not user_allows_submit
            else "platform_submit_disabled"
        )
    if screenshot_path:
        meta["screenshot_path"] = screenshot_path

    run.status = status
    run.fields_filled = result.fields_filled
    run.steps_completed = result.steps_completed
    run.captcha_solved = result.captcha_solved
    run.finished_at = datetime.utcnow()
    run.meta_json = json.dumps(meta)
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
        "needs_user": result.needs_user or status == "needs_user",
        "filled_keys": result.filled_keys,
        "ats": ats,
        "adapter": adapter.name,
        "core_ok": (result.meta or {}).get("core_ok"),
        "page_url": result.page_url,
        "resume_local_path": applicant.get("resume_local_path"),
        "screenshot_path": screenshot_path,
        "genuine_apply": bool(result.submitted),
        "submit_policy": meta["submit_policy"],
    }


async def live_fill_url(
    url: str,
    applicant: Dict[str, Any],
    *,
    ats: str | None = None,
    auto_submit: bool = False,
    user_id: int = 0,
) -> Dict[str, Any]:
    """Direct live fill against a URL (used by integration tests / ops). Never submits unless asked."""
    from playwright.async_api import async_playwright

    if not applicant.get("resume_local_path"):
        ensure_resume_local_path(user_id or 0, applicant, None)

    ats = ats or detect_ats(url)
    adapter = get_adapter(ats)
    headers = fingerprint_headers()
    proxy = playwright_proxy(user_id=user_id or None)
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
        await page.add_init_script(stealth_init_script)
        await human_delay(300, 900)
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await human_delay(1000, 1800)
        result = await adapter.fill(page, applicant, auto_submit=auto_submit)
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
    out["resume_local_path"] = applicant.get("resume_local_path")
    return out
