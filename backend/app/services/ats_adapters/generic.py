"""Generic fallback adapter for unknown ATS pages."""

from __future__ import annotations

from typing import Any, Dict

from app.services.apply_engine import answer_open_ended
from .base import AdapterResult, BaseATSAdapter


class GenericAdapter(BaseATSAdapter):
    name = "generic"
    max_steps = 3

    async def fill(self, page, applicant: Dict[str, Any], *, auto_submit: bool = False) -> AdapterResult:
        result = AdapterResult(ats=self.name, page_url=page.url)
        await self.ensure_application_form(page)
        mapping = {
            "first_name": {
                "value": applicant.get("first_name"),
                "selectors": [
                    "input[autocomplete='given-name']",
                    "input[name*='first' i]",
                    "input[id*='first' i]",
                    "input[aria-label*='First' i]",
                ],
            },
            "last_name": {
                "value": applicant.get("last_name"),
                "selectors": [
                    "input[autocomplete='family-name']",
                    "input[name*='last' i]",
                    "input[id*='last' i]",
                    "input[aria-label*='Last' i]",
                ],
            },
            "full_name": {
                "value": applicant.get("full_name"),
                "selectors": ["input[name='name']", "input[autocomplete='name']", "input[aria-label='Name']"],
            },
            "email": {
                "value": applicant.get("email"),
                "selectors": ["input[type='email']", "input[name*='email' i]", "input[autocomplete='email']"],
            },
            "phone": {
                "value": applicant.get("phone"),
                "selectors": ["input[type='tel']", "input[name*='phone' i]"],
            },
            "linkedin": {
                "value": applicant.get("linkedin"),
                "selectors": ["input[name*='linkedin' i]", "input[aria-label*='LinkedIn' i]"],
            },
        }
        result.fields_attempted = len([k for k, v in mapping.items() if v.get("value")])
        filled, keys = await self.fill_by_selectors(page, mapping)
        result.fields_filled = filled
        result.filled_keys = keys

        async def _ans(q):
            return await answer_open_ended(q, applicant, None)

        result.fields_filled += await self.answer_unlabeled_textareas(page, applicant, _ans)
        result.captcha_present = await self.detect_captcha(page)
        result.steps_completed = 1
        if auto_submit:
            if result.captcha_present and not result.captcha_solved:
                result.needs_user = True
                result.meta["blocked_reason"] = "captcha_unsolved"
            else:
                submit_result = await self.genuine_submit(page)
                result.submitted = bool(submit_result.get("submitted") or submit_result.get("confirmed"))
                result.needs_user = not result.submitted
                result.meta["submit"] = submit_result
        else:
            result.needs_user = True
        result.page_url = page.url
        return result
