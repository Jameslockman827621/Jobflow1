from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.models.user import User
from app.models.profile import UserProfile

router = APIRouter()


# Pydantic schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    
    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    location: Optional[str] = None
    desired_roles: Optional[list] = None
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    remote_only: Optional[bool] = None
    preferred_countries: Optional[list] = None
    years_of_experience: Optional[float] = None
    current_title: Optional[str] = None
    resume_text: Optional[str] = None


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    # TODO: Implement actual DB storage
    # This is a placeholder
    return UserResponse(
        id=1,
        email=user_data.email,
        is_active=True,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user():
    # TODO: Implement with auth dependency
    raise HTTPException(status_code=401, detail="Not authenticated")


@router.patch("/me/profile")
async def update_profile(profile_data: ProfileUpdate):
    # TODO: Implement
    return {"status": "profile updated"}
