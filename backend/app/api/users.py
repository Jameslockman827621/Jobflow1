"""
Users API

Note: User registration, login, and /me are handled by /api/v1/auth/*.
Profile management is handled by /api/v1/profile/*.

This router is intentionally empty to avoid conflicting stub routes that
previously shadowed the real auth/profile endpoints. Kept as an empty router
so main.py's include_router call doesn't need to change.
"""

from fastapi import APIRouter

router = APIRouter()