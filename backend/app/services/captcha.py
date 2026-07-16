"""
CAPTCHA solving via 2Captcha (and compatible providers).

Set TWOCAPTCHA_API_KEY in the environment. When unset, solve calls return
a structured "unavailable" response so apply flows can fall back to the user.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

TWOCAPTCHA_IN = "https://2captcha.com/in.php"
TWOCAPTCHA_RES = "https://2captcha.com/res.php"


class CaptchaService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "TWOCAPTCHA_API_KEY", None)

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def solve_recaptcha_v2(
        self,
        site_key: str,
        page_url: str,
        timeout_s: int = 120,
    ) -> Dict[str, Any]:
        if not self.available:
            return {"ok": False, "error": "TWOCAPTCHA_API_KEY not configured", "token": None}
        return await self._poll_solve(
            {
                "key": self.api_key,
                "method": "userrecaptcha",
                "googlekey": site_key,
                "pageurl": page_url,
                "json": 1,
            },
            timeout_s=timeout_s,
        )

    async def solve_hcaptcha(
        self,
        site_key: str,
        page_url: str,
        timeout_s: int = 120,
    ) -> Dict[str, Any]:
        if not self.available:
            return {"ok": False, "error": "TWOCAPTCHA_API_KEY not configured", "token": None}
        return await self._poll_solve(
            {
                "key": self.api_key,
                "method": "hcaptcha",
                "sitekey": site_key,
                "pageurl": page_url,
                "json": 1,
            },
            timeout_s=timeout_s,
        )

    async def solve(
        self,
        captcha_type: str,
        site_key: str,
        page_url: str,
        timeout_s: int = 120,
    ) -> Dict[str, Any]:
        captcha_type = (captcha_type or "").lower()
        if captcha_type in ("recaptcha", "recaptcha_v2", "v2"):
            return await self.solve_recaptcha_v2(site_key, page_url, timeout_s)
        if captcha_type in ("hcaptcha", "h-captcha"):
            return await self.solve_hcaptcha(site_key, page_url, timeout_s)
        return {"ok": False, "error": f"Unsupported captcha type: {captcha_type}", "token": None}

    async def _poll_solve(self, payload: Dict, timeout_s: int = 120) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                submit = await client.post(TWOCAPTCHA_IN, data=payload)
                data = submit.json()
                if data.get("status") != 1:
                    return {"ok": False, "error": data.get("request") or "submit_failed", "token": None}
                request_id = data["request"]
                elapsed = 0
                while elapsed < timeout_s:
                    await asyncio.sleep(5)
                    elapsed += 5
                    res = await client.get(
                        TWOCAPTCHA_RES,
                        params={"key": self.api_key, "action": "get", "id": request_id, "json": 1},
                    )
                    body = res.json()
                    if body.get("status") == 1:
                        return {"ok": True, "token": body.get("request"), "provider": "2captcha"}
                    if body.get("request") != "CAPCHA_NOT_READY":
                        return {"ok": False, "error": body.get("request"), "token": None}
                return {"ok": False, "error": "timeout", "token": None}
        except Exception as exc:
            logger.exception("CAPTCHA solve failed")
            return {"ok": False, "error": str(exc), "token": None}


captcha_service = CaptchaService()
