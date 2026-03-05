from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from datetime import timedelta

from app.core.config import settings
from app.core.security import create_access_token, get_current_user
from app.database import SessionLocal
from app.models.user import User
from app.models.profile import UserProfile
from app.tasks.notifications import send_welcome_email_task

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    is_active: bool
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    db = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        user = User(email=user_data.email)
        user.password = user_data.password
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create profile
        profile = UserProfile(
            user_id=user.id,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )
        db.add(profile)
        db.commit()
        
        # Send welcome email (async)
        send_welcome_email_task.delay(user.id)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_active=user.is_active,
        )
    finally:
        db.close()


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == form_data.username).first()
        
        if not user or not user.verify_password(form_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        db.close()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        return UserResponse(
            id=current_user.id,
            email=current_user.email,
            first_name=profile.first_name if profile else "",
            last_name=profile.last_name if profile else "",
            is_active=current_user.is_active,
        )
    finally:
        db.close()
