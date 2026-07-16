"""
Proxy rotation + browser fingerprint helpers for bot-detection evasion.

Configure PROXY_POOL as a comma-separated list of proxy URLs, e.g.:
  http://user:pass@host:port,http://user:pass@host2:port
"""

from __future__ import annotations

import asyncio
import hashlib
import itertools
import random
import threading
from typing import Dict, List, Optional, Set, Union
from urllib.parse import urlparse

from fake_useragent import UserAgent

from app.core.config import settings


_UA = UserAgent()
_lock = threading.Lock()
_cycle = None
_dead_proxies: Set[str] = set()


# Playwright init script to reduce automation fingerprints
stealth_init_script = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
Object.defineProperty(navigator, 'plugins', {
  get: () => [1, 2, 3, 4, 5],
});
window.chrome = window.chrome || { runtime: {} };
const originalQuery = window.navigator.permissions && window.navigator.permissions.query;
if (originalQuery) {
  window.navigator.permissions.query = (parameters) => (
    parameters && parameters.name === 'notifications'
      ? Promise.resolve({ state: Notification.permission })
      : originalQuery(parameters)
  );
}
"""


async def human_delay(min_ms: int = 200, max_ms: int = 800) -> None:
    """Async sleep for a human-like random delay between min_ms and max_ms."""
    lo = max(0, int(min_ms))
    hi = max(lo, int(max_ms))
    await asyncio.sleep(random.uniform(lo, hi) / 1000.0)


def _proxy_list() -> List[str]:
    raw = getattr(settings, "PROXY_POOL", None)
    if not raw:
        return []
    if isinstance(raw, list):
        proxies = [p.strip() for p in raw if p and str(p).strip()]
    else:
        proxies = [p.strip() for p in str(raw).split(",") if p.strip()]
    with _lock:
        return [p for p in proxies if p not in _dead_proxies]


def mark_proxy_dead(proxy: str) -> None:
    if not proxy:
        return
    with _lock:
        _dead_proxies.add(proxy)


def sticky_proxy_for_user(user_id: Optional[Union[int, str]]) -> Optional[str]:
    """Pick a stable proxy for a user via hash modulo pool size."""
    proxies = _proxy_list()
    if not proxies:
        return None
    if user_id is None:
        return next_proxy()
    digest = hashlib.sha256(str(user_id).encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % len(proxies)
    return proxies[idx]


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


def playwright_proxy(
    proxy: Optional[str] = None,
    *,
    user_id: Optional[Union[int, str]] = None,
) -> Optional[Dict]:
    """Playwright launch proxy dict. Prefer sticky proxy when user_id given."""
    if proxy is None and user_id is not None:
        proxy = sticky_proxy_for_user(user_id)
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


def _stable_rng(seed: str) -> random.Random:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def fingerprint_headers(user_id: Optional[Union[int, str]] = None) -> Dict[str, str]:
    """
    Realistic browser headers. When user_id is set, UA/platform are sticky
    so sticky proxies don't rotate fingerprints mid-session.
    """
    rng = _stable_rng(f"fp:{user_id}") if user_id is not None else random.Random()
    chrome_ver = rng.choice(["120", "121", "122", "123", "124", "125"])
    platforms = ['"Windows"', '"macOS"', '"Linux"']
    platform = rng.choice(platforms)
    try:
        ua = _UA.chrome
    except Exception:
        ua = (
            f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            f"(KHTML, like Gecko) Chrome/{chrome_ver}.0.0.0 Safari/537.36"
        )
    # Make sticky UA when user_id present by templating chrome ver into a stable base
    if user_id is not None:
        if platform == '"Windows"':
            ua = (
                f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                f"(KHTML, like Gecko) Chrome/{chrome_ver}.0.0.0 Safari/537.36"
            )
        elif platform == '"macOS"':
            ua = (
                f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                f"(KHTML, like Gecko) Chrome/{chrome_ver}.0.0.0 Safari/537.36"
            )
        else:
            ua = (
                f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                f"(KHTML, like Gecko) Chrome/{chrome_ver}.0.0.0 Safari/537.36"
            )

    lang = rng.choice(["en-US,en;q=0.9", "en-GB,en;q=0.9", "en-US,en;q=0.8"])
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": lang,
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
    with _lock:
        dead = len(_dead_proxies)
    return {
        "enabled": bool(proxies),
        "count": len(proxies),
        "dead": dead,
        "rotation": "sticky_user_hash" if proxies else "none",
        "fingerprint": "sticky_per_user",
    }
