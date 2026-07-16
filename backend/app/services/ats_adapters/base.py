"""Shared ATS adapter contract for Playwright + extension fill plans."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AdapterResult:
    ats: str
    fields_filled: int = 0
    fields_attempted: int = 0
    steps_completed: int = 0
    captcha_present: bool = False
    captcha_solved: bool = False
    submitted: bool = False
    needs_user: bool = False
    errors: List[str] = field(default_factory=list)
    filled_keys: List[str] = field(default_factory=list)
    page_url: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ats": self.ats,
            "fields_filled": self.fields_filled,
            "fields_attempted": self.fields_attempted,
            "steps_completed": self.steps_completed,
            "captcha_present": self.captcha_present,
            "captcha_solved": self.captcha_solved,
            "submitted": self.submitted,
            "needs_user": self.needs_user,
            "errors": self.errors,
            "filled_keys": self.filled_keys,
            "page_url": self.page_url,
            "meta": self.meta,
        }


class BaseATSAdapter(ABC):
    name: str = "generic"
    max_steps: int = 4

    @abstractmethod
    async def fill(self, page, applicant: Dict[str, Any], *, auto_submit: bool = False) -> AdapterResult:
        raise NotImplementedError

    async def ensure_application_form(self, page) -> None:
        """Click Apply / open the application panel if needed."""
        for sel in [
            "a:has-text('Apply')",
            "button:has-text('Apply')",
            "text=Apply for this job",
            "a:has-text('Apply for this job')",
            "button:has-text('Apply Now')",
            "[data-qa='btn-apply']",
        ]:
            try:
                loc = page.locator(sel).first
                if await loc.count() and await loc.is_visible():
                    await loc.click(timeout=2500)
                    await page.wait_for_timeout(1200)
                    return
            except Exception:
                continue

    async def detect_captcha(self, page) -> bool:
        try:
            return bool(
                await page.locator(
                    'iframe[src*="recaptcha"], iframe[src*="hcaptcha"], .g-recaptcha, [data-sitekey]'
                ).count()
            )
        except Exception:
            return False

    async def fill_by_selectors(self, page, mapping: Dict[str, Any]) -> tuple[int, List[str]]:
        """mapping: key -> {selectors: [...], value, type?}"""
        filled = 0
        keys: List[str] = []
        for key, spec in mapping.items():
            value = spec.get("value")
            if value in (None, ""):
                continue
            selectors = spec.get("selectors") or []
            ftype = spec.get("type") or "text"
            for sel in selectors:
                try:
                    loc = page.locator(sel).first
                    if await loc.count() == 0:
                        continue
                    if not await loc.is_visible():
                        # still try file inputs which can be hidden
                        if ftype != "file":
                            continue
                    if ftype == "file":
                        # value should be a local path
                        await loc.set_input_files(str(value))
                    elif ftype == "select":
                        try:
                            await loc.select_option(label=str(value))
                        except Exception:
                            await loc.select_option(value=str(value))
                    elif ftype == "checkbox":
                        if str(value).lower() in ("1", "true", "yes", "on"):
                            await loc.check()
                    elif ftype == "radio":
                        await loc.check()
                    else:
                        await loc.click(timeout=1000)
                        await loc.fill(str(value))
                    filled += 1
                    keys.append(key)
                    break
                except Exception:
                    continue
        return filled, keys

    async def answer_unlabeled_textareas(self, page, applicant: Dict[str, Any], answer_fn) -> int:
        filled = 0
        textareas = page.locator("textarea:visible")
        count = await textareas.count()
        for i in range(min(count, 10)):
            ta = textareas.nth(i)
            try:
                name = (await ta.get_attribute("name")) or ""
                if "recaptcha" in name or "h-captcha" in name:
                    continue
                existing = await ta.input_value()
                if existing and existing.strip():
                    continue
                label = await ta.evaluate(
                    """el => {
                      if (el.labels && el.labels[0]) return el.labels[0].innerText;
                      const id = el.id;
                      if (id) {
                        const lab = document.querySelector(`label[for="${id}"]`);
                        if (lab) return lab.innerText;
                      }
                      const parent = el.closest('label, .field, .form-group, li, .application-question, [data-qa]');
                      return parent ? parent.innerText.slice(0, 280) : '';
                    }"""
                )
                if not label or len(label.strip()) < 8:
                    continue
                answer = await answer_fn(label)
                if answer:
                    await ta.fill(answer)
                    filled += 1
            except Exception:
                continue
        return filled

    async def click_next(self, page) -> bool:
        """Advance wizard without submitting."""
        from .form_helpers import click_next_only

        return await click_next_only(page)

    async def click_submit_or_next(self, page, labels: Optional[List[str]] = None) -> str:
        """Returns 'submitted' | 'next' | 'none' (legacy string API)."""
        from .form_helpers import click_next_only
        from .submit import attempt_submit_and_confirm

        labels = labels or []
        next_only = labels and not any("submit" in (t or "").lower() for t in labels)
        if next_only or (
            labels
            and all(
                any(x in (t or "").lower() for x in ("next", "continue", "review", "save"))
                for t in labels
            )
            and not any("submit" in (t or "").lower() for t in labels)
        ):
            advanced = await click_next_only(page, labels)
            return "next" if advanced else "none"

        result = await attempt_submit_and_confirm(page)
        if result.get("confirmed"):
            return "submitted"
        if result.get("action") == "clicked_next":
            return "next"
        return "none"

    async def genuine_submit(self, page) -> Dict[str, Any]:
        """Click submit and verify confirmation — used for world-class auto-apply."""
        from .submit import attempt_submit_and_confirm

        return await attempt_submit_and_confirm(page)

    async def solve_captcha(self, page, result: "AdapterResult") -> None:
        from .form_helpers import detect_and_solve_captcha

        await detect_and_solve_captcha(page, result)


def get_adapter(ats: str) -> BaseATSAdapter:
    from .greenhouse import GreenhouseAdapter
    from .lever import LeverAdapter
    from .ashby import AshbyAdapter
    from .workday import WorkdayAdapter
    from .generic import GenericAdapter

    ats = (ats or "generic").lower()
    mapping = {
        "greenhouse": GreenhouseAdapter,
        "lever": LeverAdapter,
        "ashby": AshbyAdapter,
        "workday": WorkdayAdapter,
        "workable": GenericAdapter,
        "generic": GenericAdapter,
    }
    cls = mapping.get(ats, GenericAdapter)
    return cls()
