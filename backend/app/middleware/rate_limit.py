"""Simple per-IP / per-user rate limiting (Redis when available, memory fallback)."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable, Dict, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings


class _MemoryBuckets:
    def __init__(self) -> None:
        self._data: Dict[str, list] = defaultdict(list)

    def hit(self, key: str, limit: int, window_s: int = 60) -> Tuple[bool, int]:
        now = time.time()
        bucket = self._data[key]
        cutoff = now - window_s
        self._data[key] = [t for t in bucket if t >= cutoff]
        if len(self._data[key]) >= limit:
            return False, 0
        self._data[key].append(now)
        return True, max(limit - len(self._data[key]), 0)


_memory = _MemoryBuckets()


def _redis_hit(key: str, limit: int, window_s: int = 60) -> Tuple[bool, int] | None:
    try:
        import redis

        client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=0.4, socket_timeout=0.4)
        try:
            pipe = client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_s)
            count, _ = pipe.execute()
            remaining = max(limit - int(count), 0)
            return int(count) <= limit, remaining
        finally:
            client.close()
    except Exception:
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        limit = int(getattr(settings, "RATE_LIMIT_PER_MINUTE", 120) or 0)
        if limit <= 0 or request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path or ""
        # Never rate-limit health
        if path.startswith(f"{settings.API_V1_PREFIX}/health"):
            return await call_next(request)

        auth_limit = int(getattr(settings, "RATE_LIMIT_AUTH_PER_MINUTE", 30) or 30)
        is_auth = "/auth/login" in path or "/auth/register" in path or "/auth/forgot-password" in path
        effective = auth_limit if is_auth else limit

        client_ip = request.client.host if request.client else "unknown"
        # Prefer Authorization suffix so one user doesn't share IP bucket with everyone
        auth = request.headers.get("authorization") or ""
        user_key = auth[-24:] if auth.startswith("Bearer ") and len(auth) > 30 else client_ip
        key = f"rl:{path.split('/')[3] if len(path.split('/')) > 3 else 'api'}:{user_key}"

        redis_result = _redis_hit(key, effective)
        if redis_result is None:
            allowed, remaining = _memory.hit(key, effective)
        else:
            allowed, remaining = redis_result

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "rate_limit_exceeded", "retry_after_seconds": 60},
                headers={"Retry-After": "60", "X-RateLimit-Limit": str(effective)},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(effective)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
