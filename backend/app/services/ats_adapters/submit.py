"""Submit click + confirmation detection for genuine auto-apply."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


CONFIRMATION_PATTERNS = [
    r"thank you for applying",
    r"thanks for applying",
    r"application (has been )?submitted",
    r"application received",
    r"successfully submitted",
    r"we.?ve received your application",
    r"your application was sent",
    r"application complete",
    r"you applied",
]

SUBMIT_BUTTON_TEXTS = [
    "submit application",
    "submit",
    "send application",
    "apply now",
    "send",
]


async def detect_submission_success(page) -> Dict[str, Any]:
    """Inspect page for post-submit confirmation signals."""
    try:
        url = page.url or ""
        text = ""
        try:
            text = (await page.inner_text("body"))[:4000]
        except Exception:
            text = ""
        text_l = text.lower()
        url_l = url.lower()

        matched = None
        for pat in CONFIRMATION_PATTERNS:
            if re.search(pat, text_l):
                matched = pat
                break

        url_hint = any(
            x in url_l
            for x in ("/confirmation", "/thanks", "submitted=true", "application_complete", "/thank")
        )

        # Form gone + confirmation-ish heading
        form_count = await page.locator("form").count()
        submit_still = await page.locator(
            "button:has-text('Submit application'), button:has-text('Submit Application'), #submit_app"
        ).count()

        ok = bool(matched or url_hint or (form_count == 0 and submit_still == 0 and "apply" not in text_l[:200]))
        # Be stricter: require pattern or url_hint for true success
        ok = bool(matched or url_hint)

        return {
            "confirmed": ok,
            "matched_pattern": matched,
            "url_hint": url_hint,
            "page_url": url,
            "snippet": text[:240].replace("\n", " "),
        }
    except Exception as exc:
        return {"confirmed": False, "error": str(exc)[:200]}


async def click_genuine_submit(page, labels: Optional[List[str]] = None) -> str:
    """
    Click the real submit control.
    Returns: 'clicked_submit' | 'clicked_next' | 'none'
    """
    labels = labels or SUBMIT_BUTTON_TEXTS

    # 1) Role-based with regex (Playwright Python)
    for text in labels:
        try:
            btn = page.get_by_role("button", name=re.compile(text, re.I))
            if await btn.count():
                await btn.first.click(timeout=4000)
                await page.wait_for_timeout(1500)
                return "clicked_submit" if "submit" in text or "send" in text or "apply" in text else "clicked_next"
        except Exception:
            pass
        try:
            link = page.get_by_role("link", name=re.compile(text, re.I))
            if await link.count():
                await link.first.click(timeout=4000)
                await page.wait_for_timeout(1500)
                return "clicked_submit"
        except Exception:
            pass

    # 2) CSS / text selectors common on ATS
    selectors = [
        "button:has-text('Submit application')",
        "button:has-text('Submit Application')",
        "input[type='submit'][value*='Submit' i]",
        "button[type='submit']",
        "#submit_app",
        "button.application-button",
        "button:has-text('Submit')",
        "input[type='submit']",
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.count() == 0:
                continue
            if not await loc.is_enabled():
                continue
            txt = ""
            try:
                txt = ((await loc.inner_text()) or (await loc.get_attribute("value") or "")).lower()
            except Exception:
                txt = ""
            await loc.click(timeout=4000)
            await page.wait_for_timeout(1500)
            if any(x in txt for x in ("submit", "send", "apply")) or "submit" in sel:
                return "clicked_submit"
            return "clicked_next"
        except Exception:
            continue

    return "none"


async def attempt_submit_and_confirm(page, *, wait_ms: int = 2500) -> Dict[str, Any]:
    """Click submit then verify confirmation. Core of genuine auto-apply."""
    before_url = page.url
    action = await click_genuine_submit(page)
    if action == "none":
        return {
            "submitted": False,
            "confirmed": False,
            "action": "none",
            "error": "submit_button_not_found",
        }

    await page.wait_for_timeout(wait_ms)
    # Allow navigation
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=8000)
    except Exception:
        pass

    confirmation = await detect_submission_success(page)
    submitted = action == "clicked_submit" and (
        confirmation.get("confirmed") or page.url != before_url
    )
    # If we clicked submit but no confirmation yet, still mark attempted
    return {
        "submitted": bool(submitted or confirmation.get("confirmed")),
        "confirmed": bool(confirmation.get("confirmed")),
        "action": action,
        "before_url": before_url,
        "after_url": page.url,
        "confirmation": confirmation,
    }
