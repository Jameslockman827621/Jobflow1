"""Indeed Apply adapter — Easy Apply modal + company-site handoff."""

from __future__ import annotations

import re
from typing import Any, Dict

from app.services.apply_engine import answer_open_ended
from app.services.board_classify import classify_page
from .base import AdapterResult, BaseATSAdapter
from .form_helpers import (
    attempt_genuine_submit_gated,
    click_next_only,
    core_fields_ok,
    detect_and_solve_captcha,
)
from .handoff import run_ats_handoff


class IndeedAdapter(BaseATSAdapter):
    name = "indeed"
    max_steps = 6

    async def _detect_login_wall(self, page) -> bool:
        """True only on authentic Indeed auth walls — never bare email inputs on apply forms."""
        try:
            # CSS and text engines must be queried separately (Playwright parse error otherwise)
            strong = 0
            strong += await page.locator("#login-email-input").count()
            for pat in (
                r"sign in to indeed",
                r"create an account to apply",
                r"sign in to continue",
            ):
                strong += await page.get_by_text(re.compile(pat, re.I)).count()
            if not strong:
                return False
            # Apply form already visible → not a login wall
            apply_form = await page.locator(
                "input[name='name'], #jobscale-indeed-name, "
                "button:has-text('Indeed Apply'), #indeedApplyButton, "
                "#jobscale-indeed-apply, form[id*='ia-' i]"
            ).count()
            return apply_form == 0
        except Exception:
            return False

    async def _start_apply(self, page, result: AdapterResult) -> str:
        """Returns easy_apply | external | already | none"""
        try:
            if await page.get_by_text(re.compile(r"already applied|you applied", re.I)).count():
                return "already"
        except Exception:
            pass

        for sel in [
            "button:has-text('Indeed Apply')",
            "button:has-text('Apply now')",
            "#indeedApplyButton",
            "#jobscale-indeed-apply",
            "button.ia-IndeedApplyButton",
        ]:
            try:
                loc = page.locator(sel).first
                if await loc.count() and await loc.is_visible():
                    await loc.click(timeout=4000)
                    await page.wait_for_timeout(1200)
                    return "easy_apply"
            except Exception:
                continue

        for sel in [
            "a:has-text('Apply on company site')",
            "a:has-text('Apply on company website')",
            "button:has-text('Apply on company site')",
            "#jobscale-indeed-external",
        ]:
            try:
                loc = page.locator(sel).first
                if await loc.count() and await loc.is_visible():
                    href = None
                    try:
                        href = await loc.get_attribute("href")
                    except Exception:
                        href = None
                    if href:
                        result.meta["handoff_url"] = href
                        result.meta["external_url"] = href
                    else:
                        await loc.click(timeout=3000)
                        await page.wait_for_timeout(1500)
                        result.meta["handoff_url"] = page.url
                        result.meta["external_url"] = page.url
                    return "external"
            except Exception:
                continue
        return "none"

    async def _fill_form(self, page, applicant: Dict[str, Any], result: AdapterResult) -> None:
        mapping = {
            "full_name": {
                "value": applicant.get("full_name"),
                "selectors": [
                    "input[name='name']",
                    "input[autocomplete='name']",
                    "#jobscale-indeed-name",
                ],
            },
            "first_name": {
                "value": applicant.get("first_name"),
                "selectors": [
                    "input[name='firstName']",
                    "input[autocomplete='given-name']",
                    "#jobscale-indeed-first",
                ],
            },
            "last_name": {
                "value": applicant.get("last_name"),
                "selectors": [
                    "input[name='lastName']",
                    "input[autocomplete='family-name']",
                    "#jobscale-indeed-last",
                ],
            },
            "email": {
                "value": applicant.get("email"),
                "selectors": [
                    "input[type='email']",
                    "input[name='email']",
                    "#jobscale-indeed-email",
                ],
            },
            "phone": {
                "value": applicant.get("phone"),
                "selectors": [
                    "input[type='tel']",
                    "input[name='phone']",
                    "#jobscale-indeed-phone",
                ],
            },
        }
        if applicant.get("resume_local_path"):
            mapping["resume"] = {
                "value": applicant["resume_local_path"],
                "type": "file",
                "selectors": ["input[type='file']", "#jobscale-indeed-resume"],
            }

        filled, keys = await self.fill_by_selectors(page, mapping)
        result.fields_filled += filled
        for k in keys:
            if k not in result.filled_keys:
                result.filled_keys.append(k)

        async def _ans(q):
            return await answer_open_ended(q, applicant, None)

        result.fields_filled += await self.answer_unlabeled_textareas(page, applicant, _ans)

    async def fill(self, page, applicant: Dict[str, Any], *, auto_submit: bool = False) -> AdapterResult:
        result = AdapterResult(ats=self.name, page_url=page.url)
        result.meta["apply_mode"] = "easy_apply"

        # Login wall only when apply controls absent
        if await self._detect_login_wall(page):
            # If apply button still visible, don't treat as login wall
            if not await page.locator(
                "button:has-text('Indeed Apply'), #jobscale-indeed-apply, #indeedApplyButton"
            ).count():
                result.needs_user = True
                result.meta["blocked_reason"] = "login_required"
                result.meta["apply_mode"] = "login_required"
                result.meta["connect_hint"] = (
                    "Connect Indeed from Dashboard → Board connections "
                    "(JobScale extension) so Apply can use your session."
                )
                result.errors.append("login_required")
                return result

        classification = await classify_page(page, page.url)
        result.meta["classification"] = classification

        action = await self._start_apply(page, result)
        if action == "already":
            result.meta["already_applied"] = True
            result.meta["blocked_reason"] = "already_applied"
            result.meta["skipped"] = True
            return result

        # Prefer Indeed Apply when we successfully opened it; only hand off on explicit external
        if action == "external":
            handoff_url = (
                result.meta.get("handoff_url")
                or classification.get("external_url")
                or classification.get("ats_link")
            )
            if handoff_url:
                result.meta["handoff_url"] = handoff_url
                return await run_ats_handoff(
                    page,
                    applicant,
                    handoff_url=handoff_url,
                    auto_submit=auto_submit,
                    from_board="indeed",
                )
            result.needs_user = True
            result.meta["apply_mode"] = "external_redirect"
            result.meta["blocked_reason"] = "external_redirect"
            return result

        if action == "none":
            # Form may already be on page
            if not await page.locator(
                "input[name='name'], #jobscale-indeed-name, input[type='email']"
            ).count():
                result.needs_user = True
                result.meta["blocked_reason"] = "easy_apply_unavailable"
                return result

        async def _refill():
            await self._fill_form(page, applicant, result)

        for step in range(self.max_steps):
            await self._fill_form(page, applicant, result)
            result.steps_completed = step + 1
            result.meta["core_ok"] = core_fields_ok(result.filled_keys, require_name_parts=False) or bool(
                set(result.filled_keys) & {"email", "full_name", "first_name"}
            )

            submit_btn = page.locator(
                "#jobscale-indeed-submit, "
                "button:has-text('Submit your application'), "
                "button:has-text('Submit')"
            )
            try:
                if await submit_btn.count() and await submit_btn.first.is_visible():
                    break
            except Exception:
                pass

            advanced = False
            for label in ("Continue", "Next", "Review"):
                try:
                    btn = page.get_by_role("button", name=label)
                    if await btn.count() and await btn.first.is_enabled() and await btn.first.is_visible():
                        await btn.first.click(timeout=3000)
                        await page.wait_for_timeout(900)
                        advanced = True
                        break
                except Exception:
                    continue
            if not advanced:
                advanced = await click_next_only(page)
            if not advanced:
                break

        await detect_and_solve_captcha(page, result)

        if auto_submit:
            await attempt_genuine_submit_gated(page, result, applicant, refill_fn=_refill)
            if not result.submitted:
                try:
                    text = (await page.inner_text("body")).lower()
                    if "application submitted" in text or "your application has been submitted" in text:
                        if (result.meta.get("submit") or {}).get("action") == "clicked_submit":
                            result.submitted = True
                            result.needs_user = False
                except Exception:
                    pass
        else:
            result.needs_user = True

        result.page_url = page.url
        return result
