"""Lever adapter — selectors verified on jobs.lever.co/*/apply (Wealthfront)."""

from __future__ import annotations

from typing import Any, Dict

from app.services.apply_engine import answer_open_ended
from .base import AdapterResult, BaseATSAdapter


class LeverAdapter(BaseATSAdapter):
    name = "lever"
    max_steps = 2

    async def fill(self, page, applicant: Dict[str, Any], *, auto_submit: bool = False) -> AdapterResult:
        result = AdapterResult(ats=self.name, page_url=page.url)
        # Ensure we're on /apply
        if "/apply" not in page.url and "lever.co" in page.url:
            try:
                await page.goto(page.url.rstrip("/") + "/apply", wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(1000)
            except Exception:
                await self.ensure_application_form(page)

        try:
            await page.wait_for_selector(
                "input[name='name'], input[name='email'], input[type='email'], #resume-upload-input",
                timeout=15000,
            )
        except Exception:
            await page.wait_for_timeout(1500)

        mapping = {
            "full_name": {
                "value": applicant.get("full_name"),
                "selectors": ["input[name='name']", "input[name='full_name']"],
            },
            "email": {
                "value": applicant.get("email"),
                "selectors": ["input[name='email']", "input[type='email']"],
            },
            "phone": {
                "value": applicant.get("phone"),
                "selectors": ["input[name='phone']", "input[type='tel']"],
            },
            "location": {
                "value": applicant.get("location"),
                "selectors": ["#location-input", "input[name='location']"],
            },
            "current_company": {
                "value": applicant.get("current_company"),
                "selectors": ["input[name='org']", "input[name='company']"],
            },
            "linkedin": {
                "value": applicant.get("linkedin"),
                "selectors": ["input[name=\"urls[LinkedIn]\"]", "input[name*='LinkedIn']"],
            },
            "portfolio": {
                "value": applicant.get("portfolio"),
                "selectors": ["input[name=\"urls[Portfolio]\"]", "input[name*='Portfolio']", "input[name*='GitHub']"],
            },
        }
        if applicant.get("resume_local_path"):
            mapping["resume"] = {
                "value": applicant["resume_local_path"],
                "type": "file",
                "selectors": [
                    "#resume-upload-input",
                    "input[name='resume']",
                    "input[type='file'][name*='resume' i]",
                    "input[type='file']",
                ],
            }

        result.fields_attempted = len([k for k, v in mapping.items() if v.get("value")])
        filled, keys = await self.fill_by_selectors(page, mapping)
        result.fields_filled = filled
        result.filled_keys = keys

        # Custom card fields: selects
        selects = page.locator("select:visible")
        for i in range(min(await selects.count(), 12)):
            sel = selects.nth(i)
            try:
                options = await sel.evaluate(
                    """el => Array.from(el.options).map(o => ({v:o.value, t:o.text.trim()}))"""
                )
                pick = None
                for o in options:
                    t = (o.get("t") or "").lower()
                    if t in ("yes", "no", "prefer not to say", "prefer not to answer"):
                        pick = o["v"]
                        break
                if not pick:
                    for o in options:
                        if o.get("v") and o.get("t") and o["t"].lower() not in ("", "select...", "select"):
                            pick = o["v"]
                            break
                if pick:
                    await sel.select_option(value=pick)
                    result.fields_filled += 1
                    result.filled_keys.append(f"select_{i}")
            except Exception:
                continue

        # Radios: pick best option in each unanswered group
        radio_names = await page.evaluate(
            """() => {
              const names = new Set();
              document.querySelectorAll('input[type=radio]').forEach(r => { if (r.name) names.add(r.name); });
              return Array.from(names);
            }"""
        )
        for name in (radio_names or [])[:16]:
            try:
                group = page.locator(f"input[type='radio'][name=\"{name}\"]")
                checked = page.locator(f"input[type='radio'][name=\"{name}\"]:checked")
                if await checked.count():
                    continue
                preferred = None
                count = await group.count()
                name_l = (name or "").lower()
                for i in range(count):
                    r = group.nth(i)
                    label = await r.evaluate(
                        """el => {
                          const lab = el.closest('label') || (el.id && document.querySelector(`label[for="${el.id}"]`));
                          return (lab && lab.innerText || el.value || '').trim();
                        }"""
                    )
                    label_l = (label or "").lower()
                    if "sponsor" in name_l or "visa" in name_l:
                        if label_l == "no":
                            preferred = r
                            break
                    elif "authorized" in name_l or "legally" in name_l:
                        if label_l == "yes":
                            preferred = r
                            break
                    elif label_l in ("yes", "no", "indeed", "linkedin", "other", "prefer not to say"):
                        preferred = r
                        if label_l == "yes":
                            break
                if preferred is None and count:
                    preferred = group.first
                if preferred is not None:
                    await preferred.check()
                    result.fields_filled += 1
                    result.filled_keys.append(f"radio_{name[:24]}")
            except Exception:
                continue

        async def _ans(q):
            return await answer_open_ended(q, applicant, None)

        # Answer empty textareas (cover letter / custom questions)
        ta_filled = await self.answer_unlabeled_textareas(page, applicant, _ans)
        result.fields_filled += ta_filled
        if ta_filled:
            result.filled_keys.append(f"textarea_x{ta_filled}")

        # Also fill named additional-information / comments textareas
        for sel in [
            "textarea[name='comments']",
            "textarea[name='additionalInformation']",
            "textarea[name*='additional' i]",
            "textarea[name*='cover' i]",
        ]:
            try:
                loc = page.locator(sel).first
                if await loc.count() == 0:
                    continue
                existing = await loc.input_value()
                if existing and existing.strip():
                    continue
                label = await loc.evaluate(
                    """el => (el.getAttribute('aria-label') || el.name || 'additional information')"""
                )
                ans = await _ans(label)
                if ans:
                    await loc.fill(ans[:800])
                    result.fields_filled += 1
                    result.filled_keys.append("textarea_named")
            except Exception:
                continue

        result.captcha_present = await self.detect_captcha(page)
        result.steps_completed = 1
        if auto_submit:
            action = await self.click_submit_or_next(page, ["submit application", "submit"])
            result.submitted = action == "submitted"
            result.needs_user = not result.submitted
        else:
            result.needs_user = True
        result.page_url = page.url
        result.meta["core_ok"] = all(k in result.filled_keys for k in ("full_name", "email"))
        result.meta["resume_uploaded"] = "resume" in result.filled_keys
        return result
