"""Deprecated placeholder routes — real auth/profile live under /auth and /profile."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    location: Optional[str] = None


@router.post("/register", status_code=status.HTTP_410_GONE)
async def register(user_data: UserCreate):
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Use POST /api/v1/auth/register — this placeholder never wrote to the database.",
    )


@router.get("/me", status_code=status.HTTP_410_GONE)
async def get_current_user_stub():
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Use GET /api/v1/auth/me",
    )


@router.patch("/me/profile", status_code=status.HTTP_410_GONE)
async def update_profile(profile_data: ProfileUpdate):
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Use PATCH /api/v1/profile",
    )
