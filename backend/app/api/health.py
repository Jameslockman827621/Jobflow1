from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings

router = APIRouter()


@router.get("/")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


def _check_db() -> dict:
    try:
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            return {"ok": True, "status": "up"}
        finally:
            db.close()
    except Exception as exc:
        return {"ok": False, "status": "down", "error": str(exc)[:200]}


def _check_redis() -> dict:
    try:
        import redis

        client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1.5, socket_timeout=1.5)
        try:
            client.ping()
            return {"ok": True, "status": "up"}
        finally:
            client.close()
    except Exception as exc:
        # Redis is optional for API readiness — report degraded, do not hard-fail
        return {"ok": False, "status": "degraded", "error": str(exc)[:200]}


def _captcha_available() -> bool:
    try:
        from app.services.captcha import captcha_service

        return bool(captcha_service.available)
    except Exception:
        return bool(
            getattr(settings, "TWOCAPTCHA_API_KEY", None)
            or getattr(settings, "CAPTCHA_MOCK", False)
        )


def _proxy_pool_count() -> int:
    try:
        from app.services.proxy_pool import pool_status

        return int(pool_status().get("count") or 0)
    except Exception:
        pool = getattr(settings, "PROXY_POOL", None) or []
        return len(pool) if isinstance(pool, list) else 0


def _messaging_configured() -> dict:
    try:
        from app.services.messaging import messaging_service

        status = messaging_service.status()
        whatsapp = bool(status.get("whatsapp", {}).get("configured"))
        imessage = bool(status.get("imessage", {}).get("configured"))
        return {
            "configured": whatsapp or imessage,
            "whatsapp": whatsapp,
            "imessage": imessage,
        }
    except Exception:
        return {"configured": False, "whatsapp": False, "imessage": False}


@router.get("/ready")
async def readiness_check():
    db = _check_db()
    redis_info = _check_redis()
    captcha = _captcha_available()
    proxy_count = _proxy_pool_count()
    messaging = _messaging_configured()
    headless_enabled = bool(getattr(settings, "HEADLESS_APPLY_ENABLED", True))

    # Hard-fail only when DB is down. Redis outage → degraded but still ready.
    ready = bool(db.get("ok"))
    if ready and not redis_info.get("ok"):
        overall = "degraded"
    elif ready:
        overall = "ready"
    else:
        overall = "not_ready"

    return {
        "ready": ready,
        "status": overall,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": db,
            "redis": redis_info,
            "captcha_available": captcha,
            "proxy_pool_count": proxy_count,
            "messaging": messaging,
            "headless_apply_enabled": headless_enabled,
        },
    }
