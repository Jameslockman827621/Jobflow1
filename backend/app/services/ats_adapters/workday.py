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

        # Dismiss cookie / sign-in walls / apply as guest when present
        for sel in [
            "button:has-text('Accept')",
            "button:has-text('Apply Manually')",
            "a:has-text('Apply Manually')",
            "button:has-text('Create Account')",
            "a[data-automation-id='adventureButton']",
            "button[data-automation-id='adventureButton']",
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
        email_login = page.locator("input[type='email'], input[data-automation-id*='email' i]")
        if await email_login.count() and not await page.locator(
            "[data-automation-id='legalNameSection_firstName'], input[aria-label*='First Name' i]"
        ).count():
            try:
                await email_login.first.fill(str(applicant.get("email") or ""))
                result.fields_filled += 1
                result.filled_keys.append("email_gate")
            except Exception:
                pass
            result.needs_user = True
            result.meta["workday_account_wall"] = True
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
                    ],
                }

            filled, keys = await self.fill_by_selectors(page, mapping)
            result.fields_filled += filled
            result.filled_keys.extend(keys)
            result.fields_attempted += len([k for k, v in mapping.items() if v.get("value")])

            # Selects / dropdowns (Workday often uses listboxes)
            selects = page.locator("select:visible")
            for i in range(min(await selects.count(), 10)):
                try:
                    sel = selects.nth(i)
                    options = await sel.evaluate(
                        "el => Array.from(el.options).map(o => ({v:o.value,t:o.text.trim()}))"
                    )
                    pick = next((o["v"] for o in options if o.get("v") and o.get("t") and o["t"].lower() not in ("", "select one")), None)
                    if pick:
                        await sel.select_option(value=pick)
                        result.fields_filled += 1
                except Exception:
                    pass

            async def _ans(q):
                return await answer_open_ended(q, applicant, None)

            result.fields_filled += await self.answer_unlabeled_textareas(page, applicant, _ans)

            # Next / Submit
            next_clicked = False
            for sel in [
                "[data-automation-id='bottom-navigation-next-button']",
                "button[data-automation-id='pageFooterNextButton']",
                "button:has-text('Next')",
                "button:has-text('Continue')",
                "button:has-text('Submit')",
                "button:has-text('Save and Continue')",
            ]:
                try:
                    loc = page.locator(sel).first
                    if await loc.count() and await loc.is_enabled() and await loc.is_visible():
                        txt = ""
                        try:
                            txt = (await loc.inner_text()).lower()
                        except Exception:
                            txt = ""
                        if "submit" in txt and not auto_submit:
                            result.needs_user = True
                            next_clicked = False
                            break
                        await loc.click(timeout=3000)
                        await page.wait_for_timeout(1500)
                        next_clicked = True
                        if "submit" in txt:
                            result.submitted = True
                        break
                except Exception:
                    continue

            if result.submitted or not next_clicked:
                break

        result.captcha_present = await self.detect_captcha(page)
        if not result.submitted:
            result.needs_user = True
        result.page_url = page.url
        result.meta["core_ok"] = bool(set(result.filled_keys) & {"email", "first_name", "last_name"})
        result.meta["multi_step"] = True
        return result
