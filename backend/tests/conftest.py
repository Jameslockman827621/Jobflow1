import os

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-not-for-production-use-32chars",
)
# Avoid flaky 429s across the suite (Redis-backed counters accumulate)
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")
os.environ.setdefault("RATE_LIMIT_AUTH_PER_MINUTE", "0")

# Settings may already be imported by other modules; force-disable in-process too.
try:
    from app.core.config import settings

    settings.RATE_LIMIT_PER_MINUTE = 0
    settings.RATE_LIMIT_AUTH_PER_MINUTE = 0
except Exception:
    pass
