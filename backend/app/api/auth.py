import logging

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
logger = logging.getLogger(__name__)


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
    is_verified: bool = False

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


class VerifyEmailRequest(BaseModel):
    token: str


def _purpose_token(email: str, purpose: str, minutes: int = 60) -> str:
    return create_access_token(
        data={"sub": email, "purpose": purpose},
        expires_delta=timedelta(minutes=minutes),
    )


def _decode_purpose(token: str, purpose: str) -> str:
    from app.core.security import verify_token

    payload = verify_token(token)
    if not payload or payload.get("purpose") != purpose or not payload.get("sub"):
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    return str(payload["sub"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(email=user_data.email, is_verified=False)
        user.password = user_data.password

        db.add(user)
        db.commit()
        db.refresh(user)

        profile = UserProfile(
            user_id=user.id,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )
        db.add(profile)
        db.commit()

        try:
            send_welcome_email_task.delay(user.id)
        except Exception as exc:
            logger.warning("Welcome email task not queued: %s", exc)

        # Verification email (best-effort)
        try:
            from app.services.email import email_service

            vtoken = _purpose_token(user.email, "verify_email", minutes=60 * 24)
            email_service.send_verification_email(user.email, user_data.first_name, vtoken)
        except Exception as exc:
            logger.warning("Verification email failed: %s", exc)

        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_active=user.is_active,
            is_verified=bool(user.is_verified),
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
            is_verified=bool(current_user.is_verified),
        )
    finally:
        db.close()


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    """Always returns ok — does not reveal whether the email exists."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == body.email).first()
        if user and user.is_active:
            token = _purpose_token(user.email, "reset_password", minutes=60)
            try:
                from app.services.email import email_service

                email_service.send_password_reset_email(user.email, token)
            except Exception as exc:
                logger.warning("Password reset email failed: %s", exc)
        return {
            "ok": True,
            "message": "If that email is registered, a reset link has been sent.",
        }
    finally:
        db.close()


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest):
    if len(body.password or "") < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    email = _decode_purpose(body.token, "reset_password")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
        user.password = body.password
        db.commit()
        return {"ok": True, "message": "Password updated. You can sign in now."}
    finally:
        db.close()


@router.post("/send-verification")
async def send_verification(current_user: User = Depends(get_current_user)):
    if current_user.is_verified:
        return {"ok": True, "message": "Already verified", "is_verified": True}
    token = _purpose_token(current_user.email, "verify_email", minutes=60 * 24)
    from app.services.email import email_service

    profile_name = current_user.email.split("@")[0]
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if profile and profile.first_name:
            profile_name = profile.first_name
    finally:
        db.close()
    email_service.send_verification_email(current_user.email, profile_name, token)
    return {"ok": True, "message": "Verification email sent"}


@router.post("/verify-email")
async def verify_email(body: VerifyEmailRequest):
    email = _decode_purpose(body.token, "verify_email")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
        user.is_verified = True
        db.commit()
        return {"ok": True, "message": "Email verified", "is_verified": True}
    finally:
        db.close()
