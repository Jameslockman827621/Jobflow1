"""ATS handoff: when LinkedIn/Indeed/company site redirects to a real ATS, continue apply there."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.apply_engine import detect_ats
from app.services.board_classify import ATS_DIRECT
from .base import AdapterResult, get_adapter


async def run_ats_handoff(
    page,
    applicant: Dict[str, Any],
    *,
    handoff_url: str,
    auto_submit: bool = False,
    from_board: str = "generic",
) -> AdapterResult:
    """
    Navigate to handoff_url and run the destination ATS adapter.
    Returns that adapter's AdapterResult with handoff meta attached.
    """
    target_ats = detect_ats(handoff_url)
    result = AdapterResult(ats=from_board, page_url=page.url)
    result.meta["handoff_from"] = from_board
    result.meta["handoff_url"] = handoff_url
    result.meta["handoff_to"] = target_ats
    result.meta["apply_mode"] = "external_redirect"

    if target_ats not in ATS_DIRECT and target_ats not in ("generic",):
        # Still try generic on unknown company apply URLs
        target_ats = "generic"
        result.meta["handoff_to"] = target_ats

    try:
        await page.goto(handoff_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(1200)
    except Exception as exc:
        result.needs_user = True
        result.errors.append(f"handoff_nav:{exc}")
        result.meta["handoff_ok"] = False
        result.meta["blocked_reason"] = "handoff_navigation_failed"
        return result

    # Re-detect after redirects
    final_ats = detect_ats(page.url) or target_ats
    if final_ats in ATS_DIRECT:
        target_ats = final_ats
        result.meta["handoff_to"] = final_ats

    adapter = get_adapter(target_ats)
    try:
        child = await adapter.fill(page, applicant, auto_submit=auto_submit)
    except Exception as exc:
        result.needs_user = True
        result.errors.append(f"handoff_fill:{exc}")
        result.meta["handoff_ok"] = False
        return result

    # Merge child into result, preserving handoff meta
    handoff_meta = dict(result.meta)
    result = child
    result.meta = {**(child.meta or {}), **handoff_meta, "handoff_ok": True}
    result.meta["handoff_final_url"] = page.url
    return result


def extract_handoff_url(adapter_result: AdapterResult) -> Optional[str]:
    meta = adapter_result.meta or {}
    return meta.get("handoff_url") or meta.get("external_url")
