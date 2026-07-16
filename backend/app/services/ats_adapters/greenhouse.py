"""Greenhouse adapter — selectors verified on job-boards.greenhouse.io (GitLab, Cloudflare)."""

from __future__ import annotations

from typing import Any, Dict

from app.services.apply_engine import answer_open_ended
from app.services.captcha import captcha_service
from .base import AdapterResult, BaseATSAdapter


class GreenhouseAdapter(BaseATSAdapter):
    name = "greenhouse"
    max_steps = 3

    async def fill(self, page, applicant: Dict[str, Any], *, auto_submit: bool = False) -> AdapterResult:
        result = AdapterResult(ats=self.name, page_url=page.url)
        await self.ensure_application_form(page)
        await page.wait_for_timeout(800)

        mapping = {
            "first_name": {
                "value": applicant.get("first_name"),
                "selectors": ["#first_name", "input[autocomplete='given-name']", "input[aria-label='First Name']"],
            },
            "last_name": {
                "value": applicant.get("last_name"),
                "selectors": ["#last_name", "input[autocomplete='family-name']", "input[aria-label='Last Name']"],
            },
            "email": {
                "value": applicant.get("email"),
                "selectors": ["#email", "input[autocomplete='email']", "input[aria-label='Email']", "input[type='email']"],
            },
            "phone": {
                "value": applicant.get("phone"),
                "selectors": ["#phone", "input[type='tel']", "input[aria-label='Phone']"],
            },
            "linkedin": {
                "value": applicant.get("linkedin"),
                "selectors": [
                    "input[aria-label*='LinkedIn' i]",
                    "input[id^='question_'][aria-label*='LinkedIn' i]",
                ],
            },
            "full_name_pref": {
                "value": applicant.get("full_name"),
                "selectors": [
                    "input[aria-label*='name you' i]",
                    "input[aria-label*='prefer' i][aria-label*='name' i]",
                ],
            },
            "country": {
                "value": (applicant.get("location") or "").split(",")[-1].strip() if applicant.get("location") else "",
                "selectors": ["#country", "input[aria-label='Country']"],
            },
        }

        # Resume file if local path provided
        if applicant.get("resume_local_path"):
            mapping["resume"] = {
                "value": applicant["resume_local_path"],
                "type": "file",
                "selectors": ["#resume", "input[type='file'][id*='resume' i]", "input[type='file']"],
            }

        result.fields_attempted = len([k for k, v in mapping.items() if v.get("value")])
        filled, keys = await self.fill_by_selectors(page, mapping)
        result.fields_filled += filled
        result.filled_keys.extend(keys)

        # Custom Greenhouse questions (id^=question_)
        question_inputs = page.locator("input[id^='question_'], textarea[id^='question_']")
        qcount = await question_inputs.count()
        for i in range(min(qcount, 20)):
            el = question_inputs.nth(i)
            try:
                existing = await el.input_value()
                if existing and existing.strip():
                    continue
                label = await el.evaluate(
                    """el => (el.getAttribute('aria-label') || (el.labels && el.labels[0] && el.labels[0].innerText) || '').slice(0,300)"""
                )
                label_l = (label or "").lower()
                if "linkedin" in label_l and applicant.get("linkedin"):
                    await el.fill(str(applicant["linkedin"]))
                    result.fields_filled += 1
                    result.filled_keys.append("linkedin_q")
                    continue
                if "sponsor" in label_l or "visa" in label_l:
                    await el.fill("No")
                    result.fields_filled += 1
                    result.filled_keys.append("sponsorship_q")
                    continue
                if "authorized" in label_l or "legally" in label_l:
                    await el.fill("Yes")
                    result.fields_filled += 1
                    result.filled_keys.append("work_auth_q")
                    continue
                if len(label_l) > 12:
                    ans = await answer_open_ended(label, applicant, None)
                    if ans:
                        await el.fill(ans[:500])
                        result.fields_filled += 1
                        result.filled_keys.append(f"open_q_{i}")
            except Exception as exc:
                result.errors.append(str(exc)[:200])

        # Yes/No custom dropdowns rendered as text inputs with listboxes — best-effort skip

        # reCAPTCHA iframes often hydrate after fields
        await page.wait_for_timeout(1500)
        result.captcha_present = await self.detect_captcha(page)
        if result.captcha_present and captcha_service.available:
            try:
                sitekey = await page.evaluate(
                    """() => {
                      const el = document.querySelector('[data-sitekey]');
                      if (el) return el.getAttribute('data-sitekey');
                      const iframe = document.querySelector('iframe[src*="recaptcha"]');
                      if (!iframe) return null;
                      const m = (iframe.getAttribute('src')||'').match(/[?&]k=([^&]+)/);
                      return m ? m[1] : null;
                    }"""
                )
                if sitekey:
                    solved = await captcha_service.solve_recaptcha_v2(sitekey, page.url)
                    if solved.get("ok") and solved.get("token"):
                        await page.evaluate(
                            """(token) => {
                              document.querySelectorAll(
                                '#g-recaptcha-response, [name="g-recaptcha-response"], textarea[name="g-recaptcha-response"]'
                              ).forEach(el => { el.value = token; el.dispatchEvent(new Event('input', {bubbles:true})); });
                            }""",
                            solved["token"],
                        )
                        result.captcha_solved = True
            except Exception as exc:
                result.errors.append(f"captcha:{exc}")

        result.steps_completed = 1
        if auto_submit:
            action = await self.click_submit_or_next(
                page, ["submit application", "submit", "send application"]
            )
            result.submitted = action == "submitted"
            result.needs_user = not result.submitted
        else:
            # Never auto-submit by default — world-class still needs user/CAPTCHA confirm
            result.needs_user = True
            if result.captcha_present and not result.captcha_solved:
                result.needs_user = True

        result.page_url = page.url
        result.meta["required_core"] = ["first_name", "last_name", "email"]
        result.meta["core_ok"] = all(k in result.filled_keys for k in ("first_name", "last_name", "email"))
        return result
