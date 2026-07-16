"""
Server-side (headless) apply worker using Playwright.

Users can walk away — the worker fills multi-step ATS forms, solves CAPTCHAs
when configured, and reports status back to ApplyRun / Application rows.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.application import Application
from app.models.company import ApplyRun
from app.models.job import Job
from app.models.user import User
from app.services.apply_engine import build_apply_package, answer_open_ended
from app.services.captcha import captcha_service
from app.services.proxy_pool import fingerprint_headers, playwright_proxy

logger = logging.getLogger(__name__)


async def _fill_visible_fields(page, plan: Dict[str, Any], applicant: Dict[str, Any]) -> int:
    filled = 0
    for field in plan.get("fields", []):
        key = field.get("key")
        value = field.get("value")
        ftype = field.get("type")
        if value in (None, ""):
            continue
        selectors = []
        if key:
            selectors.extend(
                [
                    f'input[name*="{key}" i]',
                    f'textarea[name*="{key}" i]',
                    f'select[name*="{key}" i]',
                    f'input[id*="{key}" i]',
                    f'textarea[id*="{key}" i]',
                    f'select[id*="{key}" i]',
                    f'input[placeholder*="{key.replace("_", " ")}" i]',
                    f'textarea[placeholder*="{key.replace("_", " ")}" i]',
                    f'input[autocomplete="{key}"]',
                ]
            )
        if ftype == "email":
            selectors.append('input[type="email"]')
        if ftype == "tel":
            selectors.append('input[type="tel"]')
        if ftype == "file":
            # File upload requires local path; headless uses URL download when possible
            continue

        for sel in selectors:
            try:
                loc = page.locator(sel).first
                if await loc.count() == 0:
                    continue
                tag = await loc.evaluate("el => el.tagName.toLowerCase()")
                input_type = await loc.evaluate("el => (el.getAttribute('type') || '').toLowerCase()")
                if tag == "select":
                    try:
                        await loc.select_option(label=str(value))
                    except Exception:
                        await loc.select_option(value=str(value))
                elif input_type in ("radio",):
                    await loc.check()
                elif input_type in ("checkbox",):
                    if str(value).lower() in ("1", "true", "yes", "on"):
                        await loc.check()
                else:
                    await loc.fill(str(value))
                filled += 1
                break
            except Exception:
                continue
    return filled


async def _click_next(page, plan: Dict[str, Any]) -> bool:
    for sel in plan.get("next_button_selectors", []):
        try:
            # Playwright :has-text is supported; CSS-only selectors too
            loc = page.locator(sel).first
            if await loc.count() == 0:
                continue
            if not await loc.is_enabled():
                continue
            await loc.click(timeout=3000)
            await page.wait_for_timeout(1200)
            return True
        except Exception:
            continue
    return False


async def _handle_captcha(page, page_url: str) -> bool:
    if not captcha_service.available:
        return False
    try:
        sitekey = await page.evaluate(
            """() => {
              const el = document.querySelector('[data-sitekey]');
              if (el) return el.getAttribute('data-sitekey');
              const iframe = document.querySelector('iframe[src*="recaptcha"], iframe[src*="hcaptcha"]');
              if (!iframe) return null;
              const src = iframe.getAttribute('src') || '';
              const m = src.match(/[?&]k=([^&]+)/);
              return m ? m[1] : null;
            }"""
        )
        if not sitekey:
            return False
        is_h = await page.locator('iframe[src*="hcaptcha"]').count()
        result = await captcha_service.solve(
            "hcaptcha" if is_h else "recaptcha_v2",
            sitekey,
            page_url,
        )
        if not result.get("ok"):
            return False
        token = result["token"]
        await page.evaluate(
            """(token) => {
              const areas = [
                document.querySelector('#g-recaptcha-response'),
                document.querySelector('[name="g-recaptcha-response"]'),
                document.querySelector('[name="h-captcha-response"]'),
                document.querySelector('textarea[name="h-captcha-response"]'),
              ].filter(Boolean);
              for (const el of areas) {
                el.value = token;
                el.dispatchEvent(new Event('input', { bubbles: true }));
              }
              if (window.___grecaptcha_cfg) {
                // best-effort callback trigger
              }
            }""",
            token,
        )
        return True
    except Exception as exc:
        logger.warning("Captcha handling failed: %s", exc)
        return False


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
    plan = package["fill_plan"]
    applicant = package["applicant"]
    ats = package["ats"]

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

    if dry_run or not getattr(settings, "HEADLESS_APPLY_ENABLED", True):
        # Still validate package end-to-end without launching a browser
        run.status = "filled" if dry_run else "queued"
        run.fields_filled = len(plan.get("fields", []))
        run.steps_completed = 1
        run.finished_at = datetime.utcnow()
        run.meta_json = json.dumps({"dry_run": True, "package_ats": ats})
        application.status = "ready_to_apply"
        application.applied_via = "headless"
        db.commit()
        return {
            "ok": True,
            "dry_run": True,
            "apply_run_id": run.id,
            "ats": ats,
            "fields_planned": len(plan.get("fields", [])),
            "package": package,
        }

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        run.status = "failed"
        run.error = "playwright_not_installed"
        run.finished_at = datetime.utcnow()
        db.commit()
        return {"ok": False, "error": "playwright_not_installed", "apply_run_id": run.id}

    filled_total = 0
    steps = 0
    captcha_ok = False
    status = "filled"

    try:
        proxy = playwright_proxy()
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
            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )
            await page.goto(job.external_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(1500)

            max_steps = int(plan.get("max_steps") or 4)
            for step in range(max_steps):
                steps = step + 1
                filled_total += await _fill_visible_fields(page, plan, applicant)

                # Open-ended textareas with unlabeled questions
                textareas = page.locator("textarea")
                count = await textareas.count()
                for i in range(min(count, 8)):
                    ta = textareas.nth(i)
                    try:
                        existing = await ta.input_value()
                        if existing and existing.strip():
                            continue
                        label = await ta.evaluate(
                            """el => {
                              const id = el.id;
                              if (id) {
                                const lab = document.querySelector(`label[for="${id}"]`);
                                if (lab) return lab.innerText;
                              }
                              const parent = el.closest('label, .field, .form-group, [data-qa]');
                              return parent ? parent.innerText.slice(0, 240) : '';
                            }"""
                        )
                        if label and len(label.strip()) > 12:
                            answer = await answer_open_ended(label, applicant, job)
                            if answer:
                                await ta.fill(answer)
                                filled_total += 1
                    except Exception:
                        continue

                if await page.locator('iframe[src*="recaptcha"], iframe[src*="hcaptcha"], .g-recaptcha').count():
                    captcha_ok = await _handle_captcha(page, job.external_url)
                    if not captcha_ok and captcha_service.available is False:
                        status = "captcha"
                        break

                if not plan.get("multi_step"):
                    break
                advanced = await _click_next(page, plan)
                if not advanced:
                    break

            if auto_submit and status == "filled":
                submitted = await _click_next(page, plan)
                if submitted:
                    status = "submitted"
                    application.status = "submitted"
                    application.stage = "applied"
                    application.submitted_at = datetime.utcnow()
                    application.applied_via = "headless"
                else:
                    status = "needs_user"
            else:
                application.status = "in_progress"
                application.applied_via = "headless"

            await browser.close()

        run.status = status
        run.fields_filled = filled_total
        run.steps_completed = steps
        run.captcha_solved = captcha_ok
        run.finished_at = datetime.utcnow()
        run.meta_json = json.dumps({"auto_submit": auto_submit, "proxy": bool(proxy)})
        db.commit()
        return {
            "ok": True,
            "apply_run_id": run.id,
            "status": status,
            "fields_filled": filled_total,
            "steps_completed": steps,
            "captcha_solved": captcha_ok,
            "ats": ats,
        }
    except Exception as exc:
        logger.exception("Headless apply failed")
        run.status = "failed"
        run.error = str(exc)[:2000]
        run.finished_at = datetime.utcnow()
        db.commit()
        return {"ok": False, "error": str(exc), "apply_run_id": run.id}
