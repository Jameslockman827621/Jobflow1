"""Generic / company-site adapter with ATS handoff detection."""

from __future__ import annotations

from typing import Any, Dict

from app.services.apply_engine import answer_open_ended, detect_ats
from app.services.board_classify import ATS_DIRECT, classify_page
from .base import AdapterResult, BaseATSAdapter
from .form_helpers import (
    advance_with_validation_recovery,
    attempt_genuine_submit_gated,
    click_next_only,
    core_fields_ok,
    detect_and_solve_captcha,
)
from .handoff import run_ats_handoff


class GenericAdapter(BaseATSAdapter):
    name = "generic"
    max_steps = 5

    async def _find_ats_handoff(self, page) -> str | None:
        """Find Greenhouse/Lever/etc apply links or iframe src on company pages."""
        try:
            return await page.evaluate(
                """() => {
                  const patterns = [
                    'greenhouse.io', 'boards.greenhouse', 'job-boards.greenhouse',
                    'lever.co', 'jobs.lever',
                    'ashbyhq.com',
                    'myworkdayjobs.com',
                    'workable.com', 'apply.workable',
                    'smartrecruiters.com', 'jobs.smartrecruiters',
                    'icims.com'
                  ];
                  for (const a of Array.from(document.querySelectorAll('a[href]'))) {
                    const h = (a.href || '').toLowerCase();
                    if (patterns.some(p => h.includes(p))) return a.href;
                  }
                  for (const f of Array.from(document.querySelectorAll('iframe[src]'))) {
                    const h = (f.src || '').toLowerCase();
                    if (patterns.some(p => h.includes(p))) return f.src;
                  }
                  const marked = document.querySelector('#jobscale-ats-handoff, a[data-jobscale-handoff]');
                  if (marked && marked.href) return marked.href;
                  return null;
                }"""
            )
        except Exception:
            return None

    async def _fill_fields(self, page, applicant: Dict[str, Any], result: AdapterResult) -> None:
        mapping = {
            "first_name": {
                "value": applicant.get("first_name"),
                "selectors": [
                    "input[autocomplete='given-name']",
                    "input[name*='first' i]",
                    "input[id*='first' i]",
                    "input[aria-label*='First' i]",
                    "#first_name",
                    "#jobscale-co-first",
                ],
            },
            "last_name": {
                "value": applicant.get("last_name"),
                "selectors": [
                    "input[autocomplete='family-name']",
                    "input[name*='last' i]",
                    "input[id*='last' i]",
                    "input[aria-label*='Last' i]",
                    "#last_name",
                    "#jobscale-co-last",
                ],
            },
            "full_name": {
                "value": applicant.get("full_name"),
                "selectors": [
                    "input[name='name']",
                    "input[autocomplete='name']",
                    "input[aria-label='Name']",
                    "#jobscale-co-name",
                ],
            },
            "email": {
                "value": applicant.get("email"),
                "selectors": [
                    "input[type='email']",
                    "input[name*='email' i]",
                    "input[autocomplete='email']",
                    "#email",
                    "#jobscale-co-email",
                ],
            },
            "phone": {
                "value": applicant.get("phone"),
                "selectors": [
                    "input[type='tel']",
                    "input[name*='phone' i]",
                    "#phone",
                    "#jobscale-co-phone",
                ],
            },
            "linkedin": {
                "value": applicant.get("linkedin"),
                "selectors": [
                    "input[name*='linkedin' i]",
                    "input[aria-label*='LinkedIn' i]",
                ],
            },
            "location": {
                "value": applicant.get("location"),
                "selectors": [
                    "input[name*='location' i]",
                    "input[autocomplete='address-level2']",
                ],
            },
        }
        if applicant.get("resume_local_path"):
            mapping["resume"] = {
                "value": applicant["resume_local_path"],
                "type": "file",
                "selectors": ["input[type='file']"],
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
        result.meta["apply_mode"] = "company_site"

        classification = await classify_page(page, page.url)
        result.meta["classification"] = classification

        # Prefer ATS handoff when company page embeds/links a known ATS
        handoff_url = classification.get("external_url") or classification.get("ats_link")
        if not handoff_url:
            handoff_url = await self._find_ats_handoff(page)
        if handoff_url and detect_ats(handoff_url) in ATS_DIRECT:
            result.meta["handoff_url"] = handoff_url
            result.meta["apply_mode"] = "external_redirect"
            return await run_ats_handoff(
                page,
                applicant,
                handoff_url=handoff_url,
                auto_submit=auto_submit,
                from_board="company_site",
            )

        await self.ensure_application_form(page)
        await page.wait_for_timeout(600)

        async def _refill():
            await self._fill_fields(page, applicant, result)

        for step in range(self.max_steps):
            await self._fill_fields(page, applicant, result)
            result.steps_completed = step + 1
            result.meta["core_ok"] = core_fields_ok(result.filled_keys) or bool(
                set(result.filled_keys) & {"email", "full_name", "first_name"}
            )
            if step == self.max_steps - 1:
                break
            adv = await advance_with_validation_recovery(page, applicant, refill_fn=_refill)
            if not adv.get("advanced"):
                # last chance next
                if not await click_next_only(page):
                    break

        await detect_and_solve_captcha(page, result)
        result.meta["core_ok"] = core_fields_ok(result.filled_keys) or bool(
            set(result.filled_keys) & {"email", "full_name"}
        )
        result.meta["resume_uploaded"] = "resume" in result.filled_keys

        if auto_submit:
            await attempt_genuine_submit_gated(page, result, applicant, refill_fn=_refill)
        else:
            result.needs_user = True
        result.page_url = page.url
        return result
