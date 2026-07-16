"""
Proxy rotation + browser fingerprint helpers for bot-detection evasion.

Configure PROXY_POOL as a comma-separated list of proxy URLs, e.g.:
  http://user:pass@host:port,http://user:pass@host2:port
"""

from __future__ import annotations

import itertools
import random
import threading
from typing import Dict, List, Optional
from urllib.parse import urlparse

from fake_useragent import UserAgent

from app.core.config import settings


_UA = UserAgent()
_lock = threading.Lock()
_cycle = None


def _proxy_list() -> List[str]:
    raw = getattr(settings, "PROXY_POOL", None)
    if not raw:
        return []
    if isinstance(raw, list):
        return [p.strip() for p in raw if p and str(p).strip()]
    return [p.strip() for p in str(raw).split(",") if p.strip()]


def next_proxy() -> Optional[str]:
    """Round-robin next proxy URL, or None if pool empty."""
    global _cycle
    proxies = _proxy_list()
    if not proxies:
        return None
    with _lock:
        if _cycle is None:
            _cycle = itertools.cycle(proxies)
        return next(_cycle)


def httpx_proxies(proxy: Optional[str] = None) -> Optional[Dict[str, str]]:
    proxy = proxy or next_proxy()
    if not proxy:
        return None
    return {"http://": proxy, "https://": proxy}


def playwright_proxy(proxy: Optional[str] = None) -> Optional[Dict]:
    """Playwright launch proxy dict."""
    proxy = proxy or next_proxy()
    if not proxy:
        return None
    parsed = urlparse(proxy)
    cfg: Dict = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
    if parsed.username:
        cfg["username"] = parsed.username
    if parsed.password:
        cfg["password"] = parsed.password
    return cfg


def fingerprint_headers() -> Dict[str, str]:
    """Realistic browser headers to reduce fingerprinting signals."""
    chrome_ver = random.choice(["120", "121", "122", "123", "124", "125"])
    platforms = [
        '"Windows"',
        '"macOS"',
        '"Linux"',
    ]
    platform = random.choice(platforms)
    return {
        "User-Agent": _UA.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.9", "en-US,en;q=0.8"]),
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Ch-Ua": f'"Chromium";v="{chrome_ver}", "Google Chrome";v="{chrome_ver}", "Not-A.Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": platform,
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "DNT": "1",
    }


def pool_status() -> Dict:
    proxies = _proxy_list()
    return {
        "enabled": bool(proxies),
        "count": len(proxies),
        "rotation": "round_robin" if proxies else "none",
    }
