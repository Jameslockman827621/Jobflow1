"""Classify job URLs / pages into apply modes for world-class board coverage."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from app.services.apply_engine import detect_ats


APPLY_MODES = (
    "easy_apply",
    "external_redirect",
    "ats_direct",
    "company_site",
    "login_required",
    "unknown",
)

ATS_DIRECT = frozenset({"greenhouse", "lever", "ashby", "workday", "workable"})


def classify_url(url: str) -> Dict[str, Any]:
    """Static classification from URL alone (before page load)."""
    url_l = (url or "").lower()
    ats = detect_ats(url)
    host = urlparse(url or "").netloc.lower()

    if ats in ATS_DIRECT:
        return {
            "board": ats,
            "ats": ats,
            "apply_mode": "ats_direct",
            "needs_session": False,
        }
    if ats == "linkedin" or "linkedin.com" in host:
        return {
            "board": "linkedin",
            "ats": "linkedin",
            "apply_mode": "easy_apply",  # preferred; page may override to external_redirect
            "needs_session": True,
        }
    if ats == "indeed" or "indeed.com" in host:
        return {
            "board": "indeed",
            "ats": "indeed",
            "apply_mode": "easy_apply",
            "needs_session": True,
        }
    return {
        "board": "company_site",
        "ats": "generic",
        "apply_mode": "company_site",
        "needs_session": False,
    }


async def classify_page(page, url: Optional[str] = None) -> Dict[str, Any]:
    """Refine classification using live DOM signals."""
    base = classify_url(url or getattr(page, "url", "") or "")
    try:
        signals = await page.evaluate(
            """() => {
              const text = (document.body && document.body.innerText || '').toLowerCase().slice(0, 8000);
              const has = (re) => re.test(text);
              const q = (sel) => !!document.querySelector(sel);
              const isVisible = (el) => {
                if (!el) return false;
                const st = window.getComputedStyle(el);
                if (st.display === 'none' || st.visibility === 'hidden' || st.opacity === '0') return false;
                const r = el.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
              };
              const findHref = (needles) => {
                const links = Array.from(document.querySelectorAll('a[href]'));
                for (const a of links) {
                  if (!isVisible(a)) continue;
                  const t = ((a.innerText || '') + ' ' + (a.getAttribute('aria-label') || '')).toLowerCase();
                  const href = a.href || '';
                  for (const n of needles) {
                    if (t.includes(n) || href.toLowerCase().includes(n.replace(/\\s+/g, ''))) {
                      return href;
                    }
                  }
                }
                return null;
              };
              const login = has(/sign in to continue|log in to apply|join linkedin|create an account to apply/)
                || q('form[action*="login"], input[name="session_key"], #username');
              const easy = has(/easy apply/) || q('button.jobs-apply-button, button[aria-label*="Easy Apply" i]');
              const indeedApply = has(/indeed apply|apply now/) && (location.hostname.includes('indeed'));
              const external = findHref([
                'apply on company website',
                'apply on company site',
                'company site',
                'continue to apply',
              ]);
              const already = has(/already applied|you applied|application submitted/);
              // ATS links on company pages
              const atsLink = (() => {
                const a = Array.from(document.querySelectorAll('a[href]'));
                for (const el of a) {
                  const h = (el.href || '').toLowerCase();
                  if (/greenhouse\\.io|lever\\.co|ashbyhq\\.com|myworkdayjobs\\.com|workable\\.com/.test(h)) {
                    return el.href;
                  }
                }
                // iframes
                for (const f of Array.from(document.querySelectorAll('iframe[src]'))) {
                  const h = (f.src || '').toLowerCase();
                  if (/greenhouse\\.io|lever\\.co|ashbyhq\\.com|myworkdayjobs\\.com|workable\\.com/.test(h)) {
                    return f.src;
                  }
                }
                return null;
              })();
              return { login, easy, indeedApply, external, already, atsLink };
            }"""
        )
    except Exception as exc:
        base["classify_error"] = str(exc)[:200]
        return base

    if signals.get("login"):
        base["apply_mode"] = "login_required"
        base["blocked_reason"] = "login_required"
    elif signals.get("already"):
        base["apply_mode"] = base.get("apply_mode") or "easy_apply"
        base["already_applied"] = True
        base["blocked_reason"] = "already_applied"
    elif signals.get("external") and not signals.get("easy"):
        base["apply_mode"] = "external_redirect"
        base["external_url"] = signals.get("external")
    elif signals.get("atsLink") and base.get("board") == "company_site":
        base["apply_mode"] = "external_redirect"
        base["external_url"] = signals.get("atsLink")
        base["handoff_hint"] = True
    elif signals.get("easy") or signals.get("indeedApply"):
        base["apply_mode"] = "easy_apply"
    elif signals.get("external"):
        # Prefer Easy Apply when both exist; else external
        if not signals.get("easy"):
            base["apply_mode"] = "external_redirect"
            base["external_url"] = signals.get("external")

    if signals.get("atsLink"):
        base["ats_link"] = signals["atsLink"]
    if signals.get("external"):
        base["external_url"] = base.get("external_url") or signals["external"]

    return base


def detect_ats_from_url(url: str) -> str:
    return detect_ats(url)


def is_ats_url(url: str) -> bool:
    return detect_ats(url) in ATS_DIRECT
