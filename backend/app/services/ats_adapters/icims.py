"""iCIMS adapter — icims.com career portal application forms."""

from __future__ import annotations

from typing import Any, Dict

from app.services.apply_engine import answer_open_ended
from .base import AdapterResult, BaseATSAdapter
from .form_helpers import (
    advance_with_validation_recovery,
    attempt_genuine_submit_gated,
    core_fields_ok,
    detect_and_solve_captcha,
)


class IcimsAdapter(BaseATSAdapter):
    name = "icims"
    max_steps = 5

    async def _fill_fields(self, page, applicant: Dict[str, Any], result: AdapterResult) -> None:
        mapping = {
            "first_name": {
                "value": applicant.get("first_name"),
                "selectors": [
                    "input[name*='firstname' i]",
                    "input[name*='FirstName' i]",
                    "input[autocomplete='given-name']",
                    "#firstname",
                    "#jobscale-icims-first",
                ],
            },
            "last_name": {
                "value": applicant.get("last_name"),
                "selectors": [
                    "input[name*='lastname' i]",
                    "input[name*='LastName' i]",
                    "input[autocomplete='family-name']",
                    "#lastname",
                    "#jobscale-icims-last",
                ],
            },
            "email": {
                "value": applicant.get("email"),
                "selectors": [
                    "input[name*='email' i]",
                    "input[type='email']",
                    "#email",
                    "#jobscale-icims-email",
                ],
            },
            "phone": {
                "value": applicant.get("phone"),
                "selectors": [
                    "input[name*='phone' i]",
                    "input[type='tel']",
                    "#jobscale-icims-phone",
                ],
            },
            "linkedin": {
                "value": applicant.get("linkedin"),
                "selectors": [
                    "input[name*='linkedin' i]",
                    "input[aria-label*='LinkedIn' i]",
                ],
            },
        }
        if applicant.get("resume_local_path"):
            mapping["resume"] = {
                "value": applicant["resume_local_path"],
                "type": "file",
                "selectors": [
                    "input[type='file']",
                    "#jobscale-icims-resume",
                ],
            }

        result.fields_attempted += len([k for k, v in mapping.items() if v.get("value")])
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
        await self.ensure_application_form(page)
        await page.wait_for_timeout(600)

        async def _refill():
            await self._fill_fields(page, applicant, result)

        for step in range(self.max_steps):
            await self._fill_fields(page, applicant, result)
            result.steps_completed = step + 1
            result.meta["core_ok"] = core_fields_ok(result.filled_keys)
            if step == self.max_steps - 1:
                break
            adv = await advance_with_validation_recovery(page, applicant, refill_fn=_refill)
            if not adv.get("advanced"):
                break

        await detect_and_solve_captcha(page, result)
        result.meta["core_ok"] = core_fields_ok(result.filled_keys)
        result.meta["resume_uploaded"] = "resume" in result.filled_keys

        if auto_submit:
            await attempt_genuine_submit_gated(page, result, applicant, refill_fn=_refill)
        else:
            result.needs_user = True
        result.page_url = page.url
        return result
