"""LinkedIn Easy Apply adapter (modal multi-step)."""

from __future__ import annotations

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


class LinkedInAdapter(BaseATSAdapter):
    name = "linkedin"
    max_steps = 8

    async def _detect_login_wall(self, page) -> bool:
        try:
            return bool(
                await page.locator(
                    "input#username, input[name='session_key'], "
                    "text=/sign in to continue/i, text=/join linkedin/i"
                ).count()
            )
        except Exception:
            return False

    async def _click_easy_apply(self, page, result: AdapterResult) -> str:
        """
        Returns: 'easy_apply' | 'external' | 'already' | 'none'
        """
        # Already applied?
        try:
            if await page.locator("text=/already applied/i, button:has-text('Applied')").count():
                return "already"
        except Exception:
            pass

        # Prefer Easy Apply over company website
        for sel in [
            "button.jobs-apply-button",
            "button[aria-label*='Easy Apply' i]",
            "button:has-text('Easy Apply')",
            "button:has-text('Continue applying')",
            "[data-live-test-easy-apply-button]",
            "#jobscale-easy-apply",  # fixture
        ]:
            try:
                loc = page.locator(sel).first
                if await loc.count() and await loc.is_visible():
                    await loc.click(timeout=4000)
                    await page.wait_for_timeout(1200)
                    result.meta["easy_apply_clicked"] = True
                    return "easy_apply"
            except Exception:
                continue

        # External company apply
        for sel in [
            "a:has-text('Apply on company website')",
            "button:has-text('Apply on company website')",
            "a:has-text('Apply on company site')",
            "#jobscale-external-apply",
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
                        result.meta["external_url"] = href
                        result.meta["handoff_url"] = href
                    else:
                        await loc.click(timeout=3000)
                        await page.wait_for_timeout(1500)
                        result.meta["external_url"] = page.url
                        result.meta["handoff_url"] = page.url
                    return "external"
            except Exception:
                continue
        return "none"

    async def _fill_modal(self, page, applicant: Dict[str, Any], result: AdapterResult) -> None:
        mapping = {
            "first_name": {
                "value": applicant.get("first_name"),
                "selectors": [
                    "input[id*='firstName' i]",
                    "input[name*='firstName' i]",
                    "input[autocomplete='given-name']",
                    "#jobscale-li-first",
                ],
            },
            "last_name": {
                "value": applicant.get("last_name"),
                "selectors": [
                    "input[id*='lastName' i]",
                    "input[name*='lastName' i]",
                    "input[autocomplete='family-name']",
                    "#jobscale-li-last",
                ],
            },
            "email": {
                "value": applicant.get("email"),
                "selectors": [
                    "input[type='email']",
                    "input[id*='email' i]",
                    "#jobscale-li-email",
                ],
            },
            "phone": {
                "value": applicant.get("phone"),
                "selectors": [
                    "input[type='tel']",
                    "input[id*='phone' i]",
                    "#jobscale-li-phone",
                ],
            },
        }
        if applicant.get("resume_local_path"):
            mapping["resume"] = {
                "value": applicant["resume_local_path"],
                "type": "file",
                "selectors": [
                    "input[type='file']",
                    "#jobscale-li-resume",
                ],
            }

        filled, keys = await self.fill_by_selectors(page, mapping)
        result.fields_filled += filled
        for k in keys:
            if k not in result.filled_keys:
                result.filled_keys.append(k)

        # Textareas / custom questions inside modal
        async def _ans(q):
            return await answer_open_ended(q, applicant, None)

        result.fields_filled += await self.answer_unlabeled_textareas(page, applicant, _ans)

        # Radios/selects: prefer Yes for work auth style questions
        try:
            selects = page.locator(".jobs-easy-apply-modal select, #jobscale-easy-apply-modal select")
            count = await selects.count()
            for i in range(min(count, 15)):
                sel = selects.nth(i)
                val = await sel.input_value()
                if val:
                    continue
                opts = await sel.evaluate(
                    """el => Array.from(el.options).map(o => ({v:o.value,t:(o.text||'').trim()}))"""
                )
                pick = None
                for o in opts:
                    t = (o.get("t") or "").lower()
                    if t in ("yes", "no", "prefer not to say"):
                        pick = o["v"] or o["t"]
                        if "yes" in t:
                            break
                if pick is not None:
                    try:
                        await sel.select_option(value=str(pick))
                        result.fields_filled += 1
                    except Exception:
                        pass
        except Exception:
            pass

    async def fill(self, page, applicant: Dict[str, Any], *, auto_submit: bool = False) -> AdapterResult:
        result = AdapterResult(ats=self.name, page_url=page.url)
        result.meta["apply_mode"] = "easy_apply"

        if await self._detect_login_wall(page):
            result.needs_user = True
            result.meta["blocked_reason"] = "login_required"
            result.meta["apply_mode"] = "login_required"
            result.meta["connect_hint"] = (
                "Connect LinkedIn from Dashboard → Board connections "
                "(JobScale extension) so Easy Apply can use your session."
            )
            result.errors.append("login_required")
            return result

        classification = await classify_page(page, page.url)
        result.meta["classification"] = classification

        action = await self._click_easy_apply(page, result)
        if action == "already":
            result.submitted = False
            result.needs_user = False
            result.meta["blocked_reason"] = "already_applied"
            result.meta["already_applied"] = True
            # Treat as success-ish for idempotency: user already applied
            result.meta["skipped"] = True
            return result

        if action == "external":
            handoff_url = result.meta.get("handoff_url") or result.meta.get("external_url")
            if handoff_url and auto_submit:
                return await run_ats_handoff(
                    page,
                    applicant,
                    handoff_url=handoff_url,
                    auto_submit=auto_submit,
                    from_board="linkedin",
                )
            result.needs_user = True
            result.meta["apply_mode"] = "external_redirect"
            result.meta["blocked_reason"] = "external_redirect"
            return result

        if action == "none":
            # Maybe modal already open
            modal = page.locator(
                ".jobs-easy-apply-modal, #jobscale-easy-apply-modal, "
                "[data-test-modal-id='easy-apply-modal']"
            )
            if not await modal.count():
                result.needs_user = True
                result.meta["blocked_reason"] = "easy_apply_unavailable"
                return result

        async def _refill():
            await self._fill_modal(page, applicant, result)

        for step in range(self.max_steps):
            await self._fill_modal(page, applicant, result)
            result.steps_completed = step + 1
            result.meta["core_ok"] = core_fields_ok(result.filled_keys) or bool(
                set(result.filled_keys) & {"email", "phone", "first_name"}
            )

            # Review / Submit — only if visible (hidden step-2 buttons must not short-circuit)
            submit_like = page.locator(
                "button:has-text('Submit application'), "
                "button:has-text('Submit Application'), "
                "button[aria-label*='Submit application' i], "
                "#jobscale-li-submit"
            )
            try:
                if await submit_like.count() and await submit_like.first.is_visible() and auto_submit:
                    break
            except Exception:
                pass

            # Next / Continue / Review in modal
            advanced = False
            for label in ("Next", "Continue", "Review", "Review your application"):
                try:
                    btn = page.get_by_role("button", name=label)
                    if await btn.count() and await btn.first.is_enabled() and await btn.first.is_visible():
                        await btn.first.click(timeout=3000)
                        await page.wait_for_timeout(1000)
                        advanced = True
                        break
                except Exception:
                    continue
            if not advanced:
                advanced = await click_next_only(page)
            if not advanced:
                break
            # Re-fill after advancing (don't click Next again inside recovery)
            await _refill()
            errors = await page.locator('[aria-invalid="true"]').count()
            if errors:
                await _refill()

        await detect_and_solve_captcha(page, result)
        result.meta["core_ok"] = core_fields_ok(result.filled_keys) or bool(
            set(result.filled_keys) & {"email", "phone", "first_name", "full_name"}
        )

        if auto_submit:
            # LinkedIn confirmation can be "Application sent" — never bare "applied"
            # (Easy Apply review pages often contain the word "applied" / "Easy Apply").
            await attempt_genuine_submit_gated(page, result, applicant, refill_fn=_refill)
            if not result.submitted:
                try:
                    text = (await page.inner_text("body")).lower()
                    strong = (
                        "application sent",
                        "your application was sent",
                        "your application was submitted",
                        "application successfully submitted",
                    )
                    if any(x in text for x in strong):
                        if (result.meta.get("submit") or {}).get("action") == "clicked_submit":
                            result.submitted = True
                            result.needs_user = False
                            result.meta["linkedin_confirm"] = True
                        else:
                            result.meta["linkedin_confirm_ignored"] = "no_clicked_submit"
                    elif "applied" in text and (result.meta.get("submit") or {}).get("action") == "clicked_submit":
                        # Ambiguous — do NOT mark submitted
                        result.needs_user = True
                        result.meta["submit_uncertain"] = True
                        result.meta["blocked_reason"] = "submit_unconfirmed"
                        result.meta["linkedin_confirm_ignored"] = "weak_applied_only"
                except Exception:
                    pass
        else:
            result.needs_user = True

        result.page_url = page.url
        return result
