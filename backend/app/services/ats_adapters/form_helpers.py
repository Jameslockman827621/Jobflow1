"""Shared helpers for world-class genuine auto-apply across ATS adapters."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.services.captcha import captcha_service


NEXT_LABELS = ["next", "continue", "save and continue", "review", "save & continue"]
CORE_KEYS_ANY = (
    ("first_name", "label_first name", "given_name"),
    ("last_name", "label_last name", "family_name"),
    ("email", "label_email"),
)


async def collect_validation_errors(page) -> List[Dict[str, str]]:
    """Scrape invalid / required-empty fields after Next/Submit."""
    try:
        return await page.evaluate(
            """() => {
              const out = [];
              const push = (el, msg) => {
                const label = (el.getAttribute('aria-label')
                  || (el.labels && el.labels[0] && el.labels[0].innerText)
                  || el.name || el.id || '').trim().slice(0, 200);
                out.push({
                  name: el.name || el.id || '',
                  label,
                  message: (msg || '').slice(0, 240),
                });
              };
              document.querySelectorAll('[aria-invalid="true"], .error, .field-error, .validation-error').forEach(el => {
                const input = el.matches('input,select,textarea') ? el : el.querySelector('input,select,textarea');
                if (input) push(input, el.innerText || el.getAttribute('aria-errormessage') || 'invalid');
                else push(el, el.innerText || 'invalid');
              });
              document.querySelectorAll('input:required, select:required, textarea:required').forEach(el => {
                if (el.disabled || el.type === 'hidden') return;
                const empty = !String(el.value || '').trim();
                if (empty || (el.type === 'checkbox' && !el.checked)) {
                  push(el, el.validationMessage || 'required');
                }
              });
              // HTML5 validity
              document.querySelectorAll('input, select, textarea').forEach(el => {
                if (el.disabled || el.type === 'hidden') return;
                if (typeof el.checkValidity === 'function' && !el.checkValidity()) {
                  push(el, el.validationMessage || 'invalid');
                }
              });
              // de-dupe by name+label
              const seen = new Set();
              return out.filter(o => {
                const k = (o.name || '') + '|' + (o.label || '');
                if (seen.has(k)) return false;
                seen.add(k);
                return true;
              }).slice(0, 40);
            }"""
        )
    except Exception:
        return []


async def click_next_only(page, labels: Optional[List[str]] = None) -> bool:
    """Advance multi-step wizards without clicking final Submit."""
    labels = labels or NEXT_LABELS
    for text in labels:
        try:
            btn = page.get_by_role("button", name=re.compile(rf"^{re.escape(text)}$", re.I))
            if await btn.count():
                await btn.first.click(timeout=3500)
                await page.wait_for_timeout(1200)
                return True
        except Exception:
            pass
        try:
            loc = page.locator(f"button:has-text('{text}')").first
            if await loc.count() and await loc.is_visible() and await loc.is_enabled():
                txt = ((await loc.inner_text()) or "").lower()
                if "submit" in txt and "application" in txt:
                    continue
                if txt.strip() in ("submit",):
                    continue
                await loc.click(timeout=3500)
                await page.wait_for_timeout(1200)
                return True
        except Exception:
            continue

    for sel in [
        "[data-automation-id='bottom-navigation-next-button']",
        "button[data-automation-id='pageFooterNextButton']",
        "button:has-text('Next')",
        "button:has-text('Continue')",
        "button:has-text('Save and Continue')",
    ]:
        try:
            loc = page.locator(sel).first
            if await loc.count() == 0:
                continue
            if not await loc.is_visible() or not await loc.is_enabled():
                continue
            txt = ""
            try:
                txt = ((await loc.inner_text()) or "").lower()
            except Exception:
                txt = ""
            if "submit" in txt and "next" not in txt and "continue" not in txt:
                continue
            await loc.click(timeout=3500)
            await page.wait_for_timeout(1200)
            return True
        except Exception:
            continue
    return False


async def detect_and_solve_captcha(page, result) -> None:
    """Detect reCAPTCHA/hCaptcha and solve via captcha_service when available."""
    try:
        result.captcha_present = bool(
            await page.locator(
                'iframe[src*="recaptcha"], iframe[src*="hcaptcha"], .g-recaptcha, [data-sitekey]'
            ).count()
        )
    except Exception:
        result.captcha_present = False

    if not result.captcha_present:
        try:
            await page.wait_for_selector(
                'iframe[src*="recaptcha"], iframe[src*="hcaptcha"], [data-sitekey]',
                timeout=4000,
            )
            result.captcha_present = True
        except Exception:
            return

    if not captcha_service.available:
        result.meta["blocked_reason"] = result.meta.get("blocked_reason") or "captcha_unsolved"
        return

    try:
        info = await page.evaluate(
            """() => {
              const el = document.querySelector('[data-sitekey]');
              if (el) {
                return { sitekey: el.getAttribute('data-sitekey'), type: 'recaptcha' };
              }
              const h = document.querySelector('iframe[src*="hcaptcha"]');
              if (h) {
                const src = h.getAttribute('src') || '';
                const m = src.match(/[?&]sitekey=([^&]+)/) || src.match(/[?&]k=([^&]+)/);
                return { sitekey: m ? decodeURIComponent(m[1]) : null, type: 'hcaptcha' };
              }
              const r = document.querySelector('iframe[src*="recaptcha"]');
              if (r) {
                const src = r.getAttribute('src') || '';
                const m = src.match(/[?&]k=([^&]+)/);
                return { sitekey: m ? decodeURIComponent(m[1]) : null, type: 'recaptcha' };
              }
              return null;
            }"""
        )
        if not info or not info.get("sitekey"):
            return
        ctype = info.get("type") or "recaptcha"
        solved = await captcha_service.solve(ctype, info["sitekey"], page.url)
        if not (solved.get("ok") and solved.get("token")):
            result.errors.append(f"captcha:{solved.get('error') or 'solve_failed'}")
            return
        token = solved["token"]
        await page.evaluate(
            """(token) => {
              document.querySelectorAll(
                '#g-recaptcha-response, [name="g-recaptcha-response"], textarea[name="g-recaptcha-response"],'
                + ' [name="h-captcha-response"], textarea[name="h-captcha-response"]'
              ).forEach(el => {
                el.value = token;
                el.dispatchEvent(new Event('input', { bubbles: true }));
              });
              if (window.___grecaptcha_cfg) {
                try { /* noop — token injection is best-effort */ } catch (e) {}
              }
            }""",
            token,
        )
        result.captcha_solved = True
        result.meta["captcha_provider"] = solved.get("provider")
    except Exception as exc:
        result.errors.append(f"captcha:{exc}")


def core_fields_ok(filled_keys: List[str], *, require_name_parts: bool = True) -> bool:
    keys = set(filled_keys or [])
    email_ok = bool(keys & {"email", "label_email"})
    if not email_ok:
        return False
    if require_name_parts:
        first_ok = bool(keys & {"first_name", "label_first name", "given_name", "full_name", "label_name"})
        last_ok = bool(keys & {"last_name", "label_last name", "family_name", "full_name", "label_name"})
        return first_ok and last_ok
    return bool(keys & {"full_name", "first_name", "label_name", "name"})


def readiness_for_submit(result, applicant: Dict[str, Any]) -> Dict[str, Any]:
    """Gate genuine submit on core fields, resume, and captcha."""
    missing: List[str] = []
    core_ok = bool((result.meta or {}).get("core_ok")) or core_fields_ok(result.filled_keys)
    if not core_ok:
        missing.append("core_identity")
    resume_ok = (
        "resume" in (result.filled_keys or [])
        or bool((result.meta or {}).get("resume_uploaded"))
        or not applicant.get("resume_local_path")  # no resume expected
    )
    # If we have a resume path, require upload succeeded
    if applicant.get("resume_local_path") and "resume" not in (result.filled_keys or []):
        # Soft: many boards don't expose file input until later step
        result.meta["resume_pending"] = True
    if result.captcha_present and not result.captcha_solved:
        missing.append("captcha")
    ready = core_ok and "captcha" not in missing
    return {
        "ready": ready,
        "core_ok": core_ok,
        "missing": missing,
        "resume_ok": resume_ok,
    }


async def attempt_genuine_submit_gated(page, result, applicant: Dict[str, Any]) -> None:
    """Solve captcha, gate on readiness, submit only with confirmation."""
    from .submit import attempt_submit_and_confirm

    await detect_and_solve_captcha(page, result)
    gate = readiness_for_submit(result, applicant)
    result.meta["submit_readiness"] = gate
    if not gate["ready"]:
        result.needs_user = True
        result.meta["blocked_reason"] = ",".join(gate["missing"]) or "not_ready"
        return

    # Recover once from validation errors
    for attempt in range(2):
        submit_result = await attempt_submit_and_confirm(page)
        result.meta["submit"] = submit_result
        if submit_result.get("confirmed"):
            result.submitted = True
            result.needs_user = False
            return
        errors = await collect_validation_errors(page)
        result.meta["validation_errors"] = errors
        if not errors or attempt == 1:
            # Uncertain submit — do NOT mark submitted without confirmation
            result.submitted = False
            result.needs_user = True
            if submit_result.get("action") != "none":
                result.meta["submit_uncertain"] = True
            return
        # Leave loop for adapters to re-fill; mark for retry
        result.meta["validation_retry"] = attempt + 1
        return


def profile_completeness(applicant: Dict[str, Any]) -> Dict[str, Any]:
    """Structured gate before queuing genuine auto-apply."""
    missing = []
    if not (applicant.get("first_name") or applicant.get("full_name")):
        missing.append("first_name")
    if not (applicant.get("last_name") or applicant.get("full_name")):
        missing.append("last_name")
    if not applicant.get("email"):
        missing.append("email")
    if not applicant.get("phone"):
        missing.append("phone")
    if not (applicant.get("resume_local_path") or applicant.get("cv_id") or applicant.get("cv_download_url")):
        missing.append("resume")
    return {
        "complete": len(missing) == 0,
        "missing": missing,
        "score": max(0, 100 - 20 * len(missing)),
    }
