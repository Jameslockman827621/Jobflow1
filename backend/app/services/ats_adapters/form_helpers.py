"""Shared helpers for world-class genuine auto-apply across ATS adapters."""

from __future__ import annotations

import re
from typing import Any, Awaitable, Callable, Dict, List, Optional

from app.services.captcha import captcha_service


NEXT_LABELS = ["next", "continue", "save and continue", "review", "save & continue"]

# Structured blocked_reason codes for dashboards / batch aggregation
BLOCK_CAPTCHA = "captcha_unsolved"
BLOCK_PROFILE = "profile_incomplete"
BLOCK_VALIDATION = "validation_failed"
BLOCK_NOT_READY = "not_ready"
BLOCK_ACCOUNT_WALL = "account_wall"
BLOCK_CORE = "core_identity"

RefillFn = Callable[[], Awaitable[None]]


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
              document.querySelectorAll('input, select, textarea').forEach(el => {
                if (el.disabled || el.type === 'hidden') return;
                if (typeof el.checkValidity === 'function' && !el.checkValidity()) {
                  push(el, el.validationMessage || 'invalid');
                }
              });
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


async def refill_from_validation_errors(
    page,
    applicant: Dict[str, Any],
    errors: List[Dict[str, str]],
) -> int:
    """Best-effort refill of fields called out by validation errors."""
    filled = 0
    for err in errors or []:
        label = (err.get("label") or err.get("name") or "").lower()
        name = (err.get("name") or "").lower()
        key = label + " " + name
        value = None
        if any(x in key for x in ("first", "given")):
            value = applicant.get("first_name")
        elif any(x in key for x in ("last", "family", "surname")):
            value = applicant.get("last_name")
        elif "email" in key:
            value = applicant.get("email")
        elif any(x in key for x in ("phone", "tel", "mobile")):
            value = applicant.get("phone")
        elif "linkedin" in key:
            value = applicant.get("linkedin")
        elif any(x in key for x in ("sponsor", "visa")):
            value = "No"
        elif any(x in key for x in ("authorized", "legally", "work auth")):
            value = "Yes"
        elif any(x in key for x in ("name",)) and not any(x in key for x in ("company", "user")):
            value = applicant.get("full_name")
        elif any(x in key for x in ("location", "city")):
            value = applicant.get("location")
        if value in (None, ""):
            continue
        # Prefer named control
        try:
            if err.get("name"):
                loc = page.locator(f"[name='{err['name']}'], #{err['name']}").first
                if await loc.count():
                    await loc.fill(str(value))
                    filled += 1
                    continue
        except Exception:
            pass
        try:
            loc = page.get_by_label(re.compile(re.escape((err.get("label") or "")[:40]), re.I))
            if await loc.count():
                await loc.first.fill(str(value))
                filled += 1
        except Exception:
            continue
    return filled


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


async def advance_with_validation_recovery(
    page,
    applicant: Dict[str, Any],
    refill_fn: Optional[RefillFn] = None,
) -> Dict[str, Any]:
    """Click Next, then refill once if validation errors appear."""
    advanced = await click_next_only(page)
    if not advanced:
        return {"advanced": False, "validation_errors": [], "refilled": 0}
    errors = await collect_validation_errors(page)
    refilled = 0
    if errors:
        if refill_fn:
            await refill_fn()
            refilled = -1  # adapter-managed
        else:
            refilled = await refill_from_validation_errors(page, applicant, errors)
        # Try advancing again after refill
        if refilled:
            advanced2 = await click_next_only(page)
            errors = await collect_validation_errors(page)
            return {
                "advanced": advanced2,
                "validation_errors": errors,
                "refilled": refilled,
                "retried": True,
            }
    return {"advanced": True, "validation_errors": errors, "refilled": refilled}


async def detect_and_solve_captcha(page, result) -> None:
    """Detect reCAPTCHA/hCaptcha and solve via captcha_service when available.

    Fast path: if no captcha markers on first query, return immediately
    (no multi-second wait_for_selector tax on every application).
    """
    try:
        result.captcha_present = bool(
            await page.locator(
                'iframe[src*="recaptcha"], iframe[src*="hcaptcha"], .g-recaptcha, [data-sitekey]'
            ).count()
        )
    except Exception:
        result.captcha_present = False

    if not result.captcha_present:
        return

    if not captcha_service.available:
        result.meta["blocked_reason"] = result.meta.get("blocked_reason") or BLOCK_CAPTCHA
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
            result.meta["blocked_reason"] = BLOCK_CAPTCHA
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
              try {
                if (typeof ___grecaptcha_cfg !== 'undefined') {
                  const clients = ___grecaptcha_cfg.clients || {};
                  Object.keys(clients).forEach(k => {
                    const c = clients[k];
                    const walk = (obj, depth) => {
                      if (!obj || depth > 4) return;
                      if (typeof obj.callback === 'function') { try { obj.callback(token); } catch (e) {} }
                      if (typeof obj === 'object') Object.keys(obj).forEach(kk => walk(obj[kk], depth + 1));
                    };
                    walk(c, 0);
                  });
                }
              } catch (e) {}
            }""",
            token,
        )
        result.captcha_solved = True
        result.meta["captcha_provider"] = solved.get("provider")
    except Exception as exc:
        result.errors.append(f"captcha:{exc}")
        result.meta["blocked_reason"] = BLOCK_CAPTCHA


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
    """Gate genuine submit on core fields, resume, and captcha.

    Resume is soft here; ``attempt_genuine_submit_gated`` hard-blocks when the
    live page still has a file input and resume was not attached.
    """
    missing: List[str] = []
    core_ok = bool((result.meta or {}).get("core_ok")) or core_fields_ok(result.filled_keys)
    if not core_ok:
        missing.append(BLOCK_CORE)
    resume_ok = (
        "resume" in (result.filled_keys or [])
        or bool((result.meta or {}).get("resume_uploaded"))
        or not applicant.get("resume_local_path")
    )
    if applicant.get("resume_local_path") and not resume_ok:
        result.meta["resume_pending"] = True
    if result.captcha_present and not result.captcha_solved:
        missing.append(BLOCK_CAPTCHA)
    ready = core_ok and BLOCK_CAPTCHA not in missing
    return {
        "ready": ready,
        "core_ok": core_ok,
        "missing": missing,
        "resume_ok": resume_ok,
    }


async def attempt_genuine_submit_gated(
    page,
    result,
    applicant: Dict[str, Any],
    refill_fn: Optional[RefillFn] = None,
) -> None:
    """Solve captcha, gate on readiness, submit with one validation recovery loop."""
    from .submit import attempt_submit_and_confirm

    await detect_and_solve_captcha(page, result)
    gate = readiness_for_submit(result, applicant)
    # Hard-require resume when the form still exposes a file input and we had a CV file
    if (
        applicant.get("resume_local_path")
        and "resume" not in (result.filled_keys or [])
        and not (result.meta or {}).get("resume_uploaded")
    ):
        try:
            file_inputs = await page.locator("input[type='file']").count()
        except Exception:
            file_inputs = 0
        if file_inputs > 0:
            gate = dict(gate)
            gate["ready"] = False
            gate["resume_ok"] = False
            missing = list(gate.get("missing") or [])
            if "resume" not in missing:
                missing.append("resume")
            gate["missing"] = missing
            result.meta["resume_required_on_page"] = True
    result.meta["submit_readiness"] = gate
    if not gate["ready"]:
        result.needs_user = True
        result.meta["blocked_reason"] = ",".join(gate["missing"]) or BLOCK_NOT_READY
        return

    for attempt in range(2):
        submit_result = await attempt_submit_and_confirm(page)
        result.meta["submit"] = submit_result
        if submit_result.get("confirmed"):
            result.submitted = True
            result.needs_user = False
            result.meta.pop("blocked_reason", None)
            return

        errors = await collect_validation_errors(page)
        result.meta["validation_errors"] = errors
        if errors and attempt == 0:
            result.meta["validation_retry"] = 1
            if refill_fn:
                await refill_fn()
            else:
                await refill_from_validation_errors(page, applicant, errors)
            continue

        # Clicked submit but no confirmation yet — re-poll once (SPA late paint)
        if (
            attempt == 0
            and submit_result.get("action") == "clicked_submit"
            and submit_result.get("uncertain")
        ):
            result.meta["confirm_repoll"] = 1
            try:
                await page.wait_for_timeout(2000)
                from .submit import detect_submission_success

                again = await detect_submission_success(page)
                result.meta["submit"]["confirmation_repoll"] = again
                if again.get("confirmed"):
                    result.submitted = True
                    result.needs_user = False
                    result.meta["submit"]["confirmed"] = True
                    result.meta["submit"]["uncertain"] = False
                    result.meta.pop("blocked_reason", None)
                    return
            except Exception:
                pass

        result.submitted = False
        result.needs_user = True
        if errors:
            result.meta["blocked_reason"] = BLOCK_VALIDATION
        elif submit_result.get("action") != "none":
            result.meta["submit_uncertain"] = True
            result.meta["blocked_reason"] = result.meta.get("blocked_reason") or "submit_unconfirmed"
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
