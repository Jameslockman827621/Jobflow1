"""
Workday multi-step adapter.

Workday flows are typically:
  1) Start/Apply → account or guest
  2) My Experience / Resume
  3) My Information (name/email/phone/address)
  4) Application Questions
  5) Voluntary Disclosures / Review → Submit

Selectors use data-automation-id attributes common across myworkdayjobs.com.
"""

from __future__ import annotations

from typing import Any, Dict

from app.services.apply_engine import answer_open_ended
from .base import AdapterResult, BaseATSAdapter


class WorkdayAdapter(BaseATSAdapter):
    name = "workday"
    max_steps = 6

    async def _navigate_adventure_button(self, page, result: AdapterResult) -> None:
        """Follow adventureButton href via page.goto when present."""
        try:
            href = await page.evaluate(
                """() => {
                  const el = document.querySelector(
                    "a[data-automation-id='adventureButton'], button[data-automation-id='adventureButton']"
                  );
                  if (!el) return null;
                  if (el.tagName === 'A' && el.href) return el.href;
                  const nested = el.querySelector('a[href]');
                  return nested ? nested.href : null;
                }"""
            )
            if href:
                await page.goto(href, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(2000)
                result.meta["adventure_goto"] = href
                return
        except Exception as exc:
            result.errors.append(f"adventure_goto:{exc}")

        # Fallback: click the button
        for sel in [
            "a[data-automation-id='adventureButton']",
            "button[data-automation-id='adventureButton']",
        ]:
            try:
                loc = page.locator(sel).first
                if await loc.count() and await loc.is_visible():
                    await loc.click(timeout=2500)
                    await page.wait_for_timeout(1500)
                    return
            except Exception:
                pass

    async def fill(self, page, applicant: Dict[str, Any], *, auto_submit: bool = False) -> AdapterResult:
        result = AdapterResult(ats=self.name, page_url=page.url)

        # Prefer direct /apply URL (Workday SPA Apply button is flaky under automation)
        if "myworkdayjobs.com" in page.url and "/apply" not in page.url:
            apply_url = page.url.rstrip("/") + "/apply"
            try:
                await page.goto(apply_url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(3000)
            except Exception as exc:
                result.errors.append(f"apply_nav:{exc}")
                await self.ensure_application_form(page)

        # Adventure button: navigate via href when possible
        await self._navigate_adventure_button(page, result)

        # Dismiss cookie / sign-in walls / apply as guest when present
        for sel in [
            "button:has-text('Accept')",
            "button:has-text('Accept All')",
            "button:has-text('Apply Manually')",
            "a:has-text('Apply Manually')",
            "button:has-text('Apply as Guest')",
            "a:has-text('Apply as Guest')",
            "button:has-text('Continue as Guest')",
            "a:has-text('Continue as Guest')",
            "button:has-text('Autofill with Resume')",
            "button:has-text('Create Account')",
            "button:has-text('Apply')",
            "button:has-text('Continue')",
        ]:
            try:
                loc = page.locator(sel).first
                if await loc.count() and await loc.is_visible():
                    await loc.click(timeout=2500)
                    await page.wait_for_timeout(1500)
            except Exception:
                pass

        # Workday often forces account creation before fields appear
        has_identity = await page.locator(
            "[data-automation-id='legalNameSection_firstName'], input[aria-label*='First Name' i]"
        ).count()
        email_login = page.locator("input[type='email'], input[data-automation-id*='email' i]")
        sign_in_wall = await page.locator(
            "text=/sign in to your account/i, text=/create account/i, [data-automation-id*='signIn' i]"
        ).count()
        if await email_login.count() and not has_identity and sign_in_wall:
            try:
                await email_login.first.fill(str(applicant.get("email") or ""))
                result.fields_filled += 1
                result.filled_keys.append("email_gate")
            except Exception:
                pass
            # Try guest one more time after email
            for sel in [
                "button:has-text('Apply as Guest')",
                "a:has-text('Apply as Guest')",
                "button:has-text('Continue')",
            ]:
                try:
                    loc = page.locator(sel).first
                    if await loc.count() and await loc.is_visible():
                        await loc.click(timeout=2500)
                        await page.wait_for_timeout(2000)
                except Exception:
                    pass
            has_identity = await page.locator(
                "[data-automation-id='legalNameSection_firstName'], input[aria-label*='First Name' i]"
            ).count()
            if not has_identity:
                result.needs_user = True
                result.meta["workday_account_wall"] = True
                result.meta["blocked_reason"] = "workday_account_wall"
                result.steps_completed = 1
                result.page_url = page.url
                return result

        for step in range(self.max_steps):
            result.steps_completed = step + 1
            mapping = {
                "first_name": {
                    "value": applicant.get("first_name"),
                    "selectors": [
                        "[data-automation-id='legalNameSection_firstName']",
                        "input[data-automation-id*='firstName' i]",
                        "input[name*='firstName' i]",
                        "input[aria-label*='First Name' i]",
                    ],
                },
                "last_name": {
                    "value": applicant.get("last_name"),
                    "selectors": [
                        "[data-automation-id='legalNameSection_lastName']",
                        "input[data-automation-id*='lastName' i]",
                        "input[name*='lastName' i]",
                        "input[aria-label*='Last Name' i]",
                    ],
                },
                "email": {
                    "value": applicant.get("email"),
                    "selectors": [
                        "[data-automation-id='email']",
                        "input[type='email']",
                        "input[data-automation-id*='email' i]",
                        "input[aria-label*='Email' i]",
                    ],
                },
                "phone": {
                    "value": applicant.get("phone"),
                    "selectors": [
                        "[data-automation-id='phone']",
                        "input[data-automation-id*='phone' i]",
                        "input[type='tel']",
                        "input[aria-label*='Phone' i]",
                    ],
                },
                "city": {
                    "value": (applicant.get("location") or "").split(",")[0].strip(),
                    "selectors": [
                        "input[data-automation-id*='city' i]",
                        "input[aria-label*='City' i]",
                    ],
                },
                "address": {
                    "value": applicant.get("address") or applicant.get("location"),
                    "selectors": [
                        "input[data-automation-id*='addressLine1' i]",
                        "input[data-automation-id*='address' i]",
                        "input[aria-label*='Address' i]",
                    ],
                },
                "linkedin": {
                    "value": applicant.get("linkedin"),
                    "selectors": [
                        "input[aria-label*='LinkedIn' i]",
                        "input[data-automation-id*='linkedIn' i]",
                    ],
                },
            }
            if applicant.get("resume_local_path"):
                mapping["resume"] = {
                    "value": applicant["resume_local_path"],
                    "type": "file",
                    "selectors": [
                        "input[type='file']",
                        "[data-automation-id='file-upload-input-ref']",
                        "input[data-automation-id*='file' i]",
                    ],
                }

            filled, keys = await self.fill_by_selectors(page, mapping)
            result.fields_filled += filled
            result.filled_keys.extend(keys)
            result.fields_attempted += len([k for k, v in mapping.items() if v.get("value")])

            # Extra pass: any visible data-automation-id inputs still empty
            try:
                auto_ids = await page.evaluate(
                    """() => Array.from(document.querySelectorAll('[data-automation-id]'))
                      .filter(el => ['INPUT','TEXTAREA','SELECT'].includes(el.tagName) && !el.disabled)
                      .map(el => el.getAttribute('data-automation-id'))
                      .filter(Boolean)
                      .slice(0, 40)"""
                )
                for aid in auto_ids or []:
                    aid_l = aid.lower()
                    value = None
                    key = None
                    if "firstname" in aid_l:
                        value, key = applicant.get("first_name"), "first_name"
                    elif "lastname" in aid_l:
                        value, key = applicant.get("last_name"), "last_name"
                    elif "email" in aid_l:
                        value, key = applicant.get("email"), "email"
                    elif "phone" in aid_l:
                        value, key = applicant.get("phone"), "phone"
                    if not value or (key and key in result.filled_keys):
                        continue
                    try:
                        loc = page.locator(f"[data-automation-id='{aid}']").first
                        if await loc.count():
                            existing = ""
                            try:
                                existing = await loc.input_value()
                            except Exception:
                                pass
                            if existing and str(existing).strip():
                                continue
                            await loc.fill(str(value))
                            result.fields_filled += 1
                            result.filled_keys.append(key or aid)
                    except Exception:
                        continue
            except Exception:
                pass

            # Selects / dropdowns
            selects = page.locator("select:visible")
            for i in range(min(await selects.count(), 10)):
                try:
                    sel = selects.nth(i)
                    options = await sel.evaluate(
                        "el => Array.from(el.options).map(o => ({v:o.value,t:o.text.trim()}))"
                    )
                    pick = next(
                        (
                            o["v"]
                            for o in options
                            if o.get("v")
                            and o.get("t")
                            and o["t"].lower() not in ("", "select one", "select")
                        ),
                        None,
                    )
                    if pick:
                        await sel.select_option(value=pick)
                        result.fields_filled += 1
                except Exception:
                    pass

            async def _ans(q):
                return await answer_open_ended(q, applicant, None)

            result.fields_filled += await self.answer_unlabeled_textareas(page, applicant, _ans)

            # Multi-step Next only — submit happens after loop with confirmation
            from .form_helpers import click_next_only

            next_clicked = await click_next_only(page)
            if not next_clicked:
                # Submit button may be visible on final step — stop advancing
                break

        from .form_helpers import attempt_genuine_submit_gated, core_fields_ok

        result.meta["core_ok"] = core_fields_ok(result.filled_keys) or bool(
            set(result.filled_keys) & {"email", "first_name", "last_name", "email_gate"}
        )
        result.meta["multi_step"] = True
        if result.meta.get("workday_account_wall"):
            result.needs_user = True
            result.page_url = page.url
            return result

        if auto_submit:
            await attempt_genuine_submit_gated(page, result, applicant)
        else:
            result.needs_user = True
        result.page_url = page.url
        return result
