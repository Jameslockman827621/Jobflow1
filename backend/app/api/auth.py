import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from datetime import timedelta
from typing import Optional

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
    expires_in_days: Optional[int] = None


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
            detail = "Incorrect email or password"
            if user and not user.hashed_password and user.google_sub:
                detail = "This account uses Google sign-in. Continue with Google."
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=detail,
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


class GoogleTokenRequest(BaseModel):
    id_token: str


def _upsert_google_user(db, claims: dict) -> User:
    """Create or link a user from Google claims (sub + email)."""
    sub = str(claims.get("sub") or "")
    email = str(claims.get("email") or "").lower().strip()
    if not sub or not email:
        raise HTTPException(status_code=400, detail="Google account missing email")

    user = db.query(User).filter(User.google_sub == sub).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
    if user:
        user.google_sub = sub
        user.is_verified = True
        user.is_active = True
    else:
        user = User(email=email, hashed_password=None, google_sub=sub, is_verified=True)
        db.add(user)
        db.flush()
        profile = UserProfile(
            user_id=user.id,
            first_name=str(claims.get("given_name") or claims.get("name") or "").split(" ")[0] or "Google",
            last_name=str(claims.get("family_name") or ""),
        )
        db.add(profile)
    db.commit()
    db.refresh(user)
    # Ensure profile exists when linking existing email account
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        db.add(
            UserProfile(
                user_id=user.id,
                first_name=str(claims.get("given_name") or "Google"),
                last_name=str(claims.get("family_name") or ""),
            )
        )
        db.commit()
    return user


@router.get("/google")
async def google_oauth_start():
    """Return Google authorize URL (or 503 when OAuth not configured)."""
    from app.services.google_oauth import build_authorize_url, google_oauth_configured

    if not google_oauth_configured():
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )
    url, state = build_authorize_url()
    return {"authorize_url": url, "state": state}


@router.get("/google/callback")
async def google_oauth_callback(code: str = "", state: str = "", error: str = ""):
    """OAuth redirect callback — exchanges code and redirects to APP_URL with JWT."""
    from fastapi.responses import RedirectResponse
    from app.services.google_oauth import exchange_code, fetch_userinfo, google_oauth_configured

    app_url = settings.APP_URL.rstrip("/")
    if error:
        return RedirectResponse(f"{app_url}/login?oauth_error={error}")
    if not code:
        return RedirectResponse(f"{app_url}/login?oauth_error=missing_code")
    if not google_oauth_configured():
        return RedirectResponse(f"{app_url}/login?oauth_error=not_configured")

    try:
        tokens = await exchange_code(code)
        access = tokens.get("access_token")
        if not access:
            raise ValueError("no_access_token")
        claims = await fetch_userinfo(access)
        # Normalize claim keys
        claims = {
            "sub": claims.get("sub"),
            "email": claims.get("email"),
            "email_verified": claims.get("email_verified", True),
            "given_name": claims.get("given_name"),
            "family_name": claims.get("family_name"),
            "name": claims.get("name"),
        }
        db = SessionLocal()
        try:
            user = _upsert_google_user(db, claims)
            jwt = create_access_token(
                data={"sub": user.email},
                expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            )
        finally:
            db.close()
        return RedirectResponse(f"{app_url}/login?oauth_token={jwt}")
    except Exception as exc:
        logger.warning("Google OAuth callback failed: %s", exc)
        return RedirectResponse(f"{app_url}/login?oauth_error=auth_failed")


@router.post("/google/token", response_model=Token)
async def google_oauth_id_token(body: GoogleTokenRequest):
    """
    Exchange a Google ID token for a JobScale JWT (SPA / testable path).

    Verifies audience against GOOGLE_CLIENT_ID via Google tokeninfo.
    """
    from app.services import google_oauth as google_oauth_svc

    try:
        claims = await google_oauth_svc.verify_id_token(body.id_token)
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID.",
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    db = SessionLocal()
    try:
        user = _upsert_google_user(db, claims)
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        db.close()


@router.post("/extension-token", response_model=Token)
async def extension_token(current_user: User = Depends(get_current_user)):
    """
    Issue a longer-lived JWT for the Chrome extension (cookie sync / Easy Apply).

    Lifetime: ``EXTENSION_TOKEN_EXPIRE_DAYS`` (default 30). Same claims as login;
    not a purpose-scoped token.
    """
    days = max(1, int(getattr(settings, "EXTENSION_TOKEN_EXPIRE_DAYS", 30) or 30))
    access_token = create_access_token(
        data={"sub": current_user.email, "client": "extension"},
        expires_delta=timedelta(days=days),
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in_days": days,
    }


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
