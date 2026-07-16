"""Ashby adapter — jobs.ashbyhq.com application forms (React, may render slowly)."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.services.apply_engine import answer_open_ended
from .base import AdapterResult, BaseATSAdapter


class AshbyAdapter(BaseATSAdapter):
    name = "ashby"
    max_steps = 4

    async def _click_apply(self, page) -> None:
        for sel in [
            "a:has-text('Apply')",
            "button:has-text('Apply')",
            "a:has-text('Apply for this Job')",
            "button:has-text('Apply for this Job')",
            "a:has-text('Apply Now')",
            "button:has-text('Apply Now')",
            "[data-testid*='apply' i]",
        ]:
            try:
                loc = page.locator(sel).first
                if await loc.count() and await loc.is_visible():
                    await loc.click(timeout=3000)
                    await page.wait_for_timeout(1200)
                    return
            except Exception:
                continue

    async def _fill_by_label_contains(
        self,
        page,
        pairs: List[Tuple[str, Any]],
    ) -> Tuple[int, List[str]]:
        """Fill inputs whose associated label text contains a substring."""
        filled = 0
        keys: List[str] = []
        for key, value in pairs:
            if value in (None, ""):
                continue
            try:
                handle = await page.evaluate_handle(
                    """(needle) => {
                      const all = Array.from(document.querySelectorAll('input, textarea, select'));
                      const n = (needle || '').toLowerCase();
                      for (const el of all) {
                        if (el.type === 'hidden' || el.disabled) continue;
                        let label = '';
                        if (el.labels && el.labels[0]) label = el.labels[0].innerText || '';
                        else if (el.id) {
                          const lab = document.querySelector(`label[for="${el.id}"]`);
                          if (lab) label = lab.innerText || '';
                        }
                        label = (label + ' ' + (el.getAttribute('aria-label') || '')
                          + ' ' + (el.placeholder || '') + ' ' + (el.name || '')).toLowerCase();
                        if (label.includes(n)) return el;
                      }
                      return null;
                    }""",
                    key.replace("_", " "),
                )
                el = handle.as_element()
                if not el:
                    continue
                tag = await el.evaluate("el => el.tagName")
                if tag == "SELECT":
                    try:
                        await el.select_option(label=str(value))
                    except Exception:
                        await el.select_option(value=str(value))
                else:
                    await el.fill(str(value))
                filled += 1
                keys.append(f"label_{key}")
            except Exception:
                continue
        return filled, keys

    async def fill(self, page, applicant: Dict[str, Any], *, auto_submit: bool = False) -> AdapterResult:
        result = AdapterResult(ats=self.name, page_url=page.url)

        # Try clicking Apply on the job posting first
        await self._click_apply(page)

        # Navigate to /application if needed
        if "ashbyhq.com" in page.url and "/application" not in page.url:
            try:
                await page.goto(page.url.rstrip("/") + "/application", wait_until="domcontentloaded", timeout=45000)
            except Exception:
                await self.ensure_application_form(page)
                await self._click_apply(page)

        # Ashby is SPA — wait up to 20s for inputs
        try:
            await page.wait_for_selector("input, textarea, select", timeout=20000)
        except Exception:
            await self._click_apply(page)
            try:
                await page.wait_for_selector("input, textarea, select", timeout=10000)
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

        # Fallback: fill by label text contains
        label_pairs = [
            ("first name", applicant.get("first_name")),
            ("last name", applicant.get("last_name")),
            ("email", applicant.get("email")),
            ("phone", applicant.get("phone")),
            ("linkedin", applicant.get("linkedin")),
            ("name", applicant.get("full_name")),
            ("location", applicant.get("location")),
            ("company", applicant.get("current_company")),
        ]
        more, more_keys = await self._fill_by_label_contains(page, label_pairs)
        # Avoid double-counting keys already filled via selectors
        for k in more_keys:
            if k not in result.filled_keys:
                result.filled_keys.append(k)
                result.fields_filled += 1

        # Multi-step Ashby: Next only — never submit during fill loop
        from .form_helpers import attempt_genuine_submit_gated, click_next_only, core_fields_ok

        for step in range(self.max_steps - 1):
            advanced = await click_next_only(page)
            if not advanced:
                break
            result.steps_completed += 1
            await page.wait_for_timeout(1000)
            more, more_keys = await self.fill_by_selectors(page, mapping)
            result.fields_filled += more
            result.filled_keys.extend(more_keys)
            label_more, label_keys = await self._fill_by_label_contains(page, label_pairs)
            result.fields_filled += label_more
            result.filled_keys.extend(label_keys)

        async def _ans(q):
            return await answer_open_ended(q, applicant, None)

        result.fields_filled += await self.answer_unlabeled_textareas(page, applicant, _ans)
        if not result.steps_completed:
            result.steps_completed = 1
        result.meta["core_ok"] = core_fields_ok(result.filled_keys) or bool(
            set(result.filled_keys) & {"email", "label_email", "full_name"}
        )
        if auto_submit:
            await attempt_genuine_submit_gated(page, result, applicant)
        else:
            result.needs_user = True
        result.page_url = page.url
        return result
