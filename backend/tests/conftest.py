import os

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-not-for-production-use-32chars",
)
