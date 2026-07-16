"""Ashby adapter — jobs.ashbyhq.com application forms (React, may render slowly)."""

from __future__ import annotations

from typing import Any, Dict

from app.services.apply_engine import answer_open_ended
from .base import AdapterResult, BaseATSAdapter


class AshbyAdapter(BaseATSAdapter):
    name = "ashby"
    max_steps = 4

    async def fill(self, page, applicant: Dict[str, Any], *, auto_submit: bool = False) -> AdapterResult:
        result = AdapterResult(ats=self.name, page_url=page.url)
        # Navigate to /application if needed
        if "ashbyhq.com" in page.url and "/application" not in page.url:
            try:
                await page.goto(page.url.rstrip("/") + "/application", wait_until="domcontentloaded", timeout=45000)
            except Exception:
                await self.ensure_application_form(page)

        # Ashby is SPA — wait for inputs
        try:
            await page.wait_for_selector("input, textarea, select", timeout=15000)
        except Exception:
            await page.wait_for_timeout(3000)

        mapping = {
            "first_name": {
                "value": applicant.get("first_name"),
                "selectors": [
                    "input[name*='first' i]",
                    "input[autocomplete='given-name']",
                    "input[placeholder*='First' i]",
                    "input[aria-label*='First' i]",
                ],
            },
            "last_name": {
                "value": applicant.get("last_name"),
                "selectors": [
                    "input[name*='last' i]",
                    "input[autocomplete='family-name']",
                    "input[placeholder*='Last' i]",
                    "input[aria-label*='Last' i]",
                ],
            },
            "email": {
                "value": applicant.get("email"),
                "selectors": [
                    "input[type='email']",
                    "input[name*='email' i]",
                    "input[autocomplete='email']",
                    "input[aria-label*='Email' i]",
                ],
            },
            "phone": {
                "value": applicant.get("phone"),
                "selectors": [
                    "input[type='tel']",
                    "input[name*='phone' i]",
                    "input[aria-label*='Phone' i]",
                ],
            },
            "linkedin": {
                "value": applicant.get("linkedin"),
                "selectors": [
                    "input[name*='linkedin' i]",
                    "input[aria-label*='LinkedIn' i]",
                    "input[placeholder*='LinkedIn' i]",
                ],
            },
            "full_name": {
                "value": applicant.get("full_name"),
                "selectors": [
                    "input[name*='name' i]:not([name*='first' i]):not([name*='last' i])",
                    "input[aria-label='Name']",
                    "input[placeholder='Name']",
                ],
            },
        }
        if applicant.get("resume_local_path"):
            mapping["resume"] = {
                "value": applicant["resume_local_path"],
                "type": "file",
                "selectors": ["input[type='file']"],
            }

        result.fields_attempted = len([k for k, v in mapping.items() if v.get("value")])
        filled, keys = await self.fill_by_selectors(page, mapping)
        result.fields_filled = filled
        result.filled_keys = keys

        # Multi-step Ashby: keep Next until no progress
        for step in range(self.max_steps - 1):
            action = await self.click_submit_or_next(page, ["next", "continue", "submit application", "submit"])
            if action == "none":
                break
            result.steps_completed += 1
            await page.wait_for_timeout(1000)
            more, more_keys = await self.fill_by_selectors(page, mapping)
            result.fields_filled += more
            result.filled_keys.extend(more_keys)
            if action == "submitted":
                result.submitted = True
                break

        async def _ans(q):
            return await answer_open_ended(q, applicant, None)

        result.fields_filled += await self.answer_unlabeled_textareas(page, applicant, _ans)
        result.captcha_present = await self.detect_captcha(page)
        if not result.steps_completed:
            result.steps_completed = 1
        if auto_submit and not result.submitted:
            action = await self.click_submit_or_next(page, ["submit application", "submit"])
            result.submitted = action == "submitted"
        result.needs_user = not result.submitted
        result.page_url = page.url
        result.meta["core_ok"] = bool(set(result.filled_keys) & {"email", "first_name", "full_name"})
        return result
