"""
Referral System API

Users get:
- $10 Stripe customer-balance credit (when Stripe customer exists) per successful signup
- Friends get 1 month Pro trial (subscription_plan=pro + subscription_end)

Endpoints:
- GET /referrals/code - Get user's referral code
- POST /referrals/invite - Send invite to friend
- GET /referrals/stats - Get referral stats
- POST /referrals/claim - Claim referral (new user)
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from sqlalchemy.orm import Session
import secrets
import string

from app.core.config import settings
from app.database import SessionLocal
from app.core.security import get_current_user
from app.models.user import User
from app.models.referral import ReferralCode, Referral
from app.services.email import email_service
from app.services.referral_rewards import apply_referral_claim

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_referral_code() -> str:
    """Generate a unique referral code"""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))


class ReferralCodeResponse(BaseModel):
    code: str
    link: str
    total_referrals: int
    successful_referrals: int
    earnings: int  # In dollars


class InviteRequest(BaseModel):
    email: EmailStr
    message: Optional[str] = ""


class ClaimRequest(BaseModel):
    code: str


class ReferralStats(BaseModel):
    total_referrals: int
    pending: int
    registered: int
    subscribed: int
    total_earnings: int
    referrals: List[dict]


@router.get("/code", response_model=ReferralCodeResponse)
async def get_referral_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get or create user's referral code"""
    referral_code = db.query(ReferralCode).filter(
        ReferralCode.user_id == current_user.id
    ).first()
    
    if not referral_code:
        code = generate_referral_code()
        referral_code = ReferralCode(
            user_id=current_user.id,
            code=code,
        )
        db.add(referral_code)
        db.commit()
        db.refresh(referral_code)

    app_url = settings.APP_URL.rstrip("/")
    return ReferralCodeResponse(
        code=referral_code.code,
        link=f"{app_url}/login?mode=signup&ref={referral_code.code}",
        total_referrals=referral_code.total_referrals or 0,
        successful_referrals=referral_code.successful_referrals or 0,
        earnings=(referral_code.successful_referrals or 0) * 10,
    )


@router.post("/invite")
async def send_invite(
    request: InviteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send referral invite to friend"""
    referral_code = db.query(ReferralCode).filter(
        ReferralCode.user_id == current_user.id
    ).first()
    
    if not referral_code:
        raise HTTPException(status_code=404, detail="No referral code found")
    
    existing = db.query(Referral).filter(
        Referral.referrer_id == referral_code.id,
        Referral.email == request.email,
    ).first()
    
    if existing:
        return {"status": "already_sent", "message": "Invite already sent to this email"}
    
    referral = Referral(
        referrer_id=referral_code.id,
        email=request.email,
        status="pending",
    )
    db.add(referral)
    
    invite_link = f"{settings.APP_URL.rstrip('/')}/login?mode=signup&ref={referral_code.code}"
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>You've been invited to JobScale</h2>
        
        <p>{current_user.email} invited you to JobScale — AI-assisted job search and apply.</p>
        
        <div style="background: #eff6ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0 0 15px 0;"><strong>Your benefits:</strong></p>
            <ul style="margin: 0;">
                <li>1 month Pro trial on signup</li>
                <li>Matched jobs + application tracker</li>
                <li>Interview coach when OpenAI is configured</li>
            </ul>
        </div>
        
        <p style="margin-top: 20px;">
            <a href="{invite_link}" 
               style="background-color: #0f172a; color: white; padding: 12px 24px; 
                      text-decoration: none; border-radius: 6px; display: inline-block;">
                Claim your Pro trial
            </a>
        </p>
        
        {f"<p style='margin-top: 20px; color: #666;'>{request.message}</p>" if request.message else ""}
        
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;" />
        
        <p style="color: #666; font-size: 14px;">
            This invite expires in 30 days.
        </p>
    </body>
    </html>
    """
    
    email_service.send_email(request.email, "You're invited to try JobScale", html)
    
    db.commit()
    
    return {"status": "sent", "message": f"Invite sent to {request.email}", "invite_link": invite_link}


@router.get("/stats", response_model=ReferralStats)
async def get_referral_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get referral statistics"""
    referral_code = db.query(ReferralCode).filter(
        ReferralCode.user_id == current_user.id
    ).first()
    
    if not referral_code:
        return ReferralStats(
            total_referrals=0,
            pending=0,
            registered=0,
            subscribed=0,
            total_earnings=0,
            referrals=[],
        )
    
    referrals = db.query(Referral).filter(
        Referral.referrer_id == referral_code.id
    ).order_by(Referral.created_at.desc()).all()
    
    return ReferralStats(
        total_referrals=referral_code.total_referrals or 0,
        pending=len([r for r in referrals if r.status == "pending"]),
        registered=len([r for r in referrals if r.status == "registered"]),
        subscribed=len([r for r in referrals if r.status == "subscribed"]),
        total_earnings=(referral_code.successful_referrals or 0) * 10,
        referrals=[
            {
                "email": r.email,
                "status": r.status,
                "registered_at": r.registered_at.isoformat() if r.registered_at else None,
                "reward_given": bool(r.reward_given),
                "reward_amount_cents": r.reward_amount or 0,
                "reward": (
                    f"${(r.reward_amount or 1000) / 100:.0f}"
                    + (" credited" if r.reward_given else " pending")
                    if r.status in ("registered", "subscribed")
                    else "$0"
                ),
            }
            for r in referrals
        ],
    )


@router.post("/claim")
async def claim_referral(
    body: ClaimRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Claim a referral code — grants Pro trial + queues referrer Stripe credit."""
    code = (body.code or "").strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Referral code required")
    try:
        referral, referral_code, meta = apply_referral_claim(
            db, code=code, claimant=current_user
        )
    except ValueError as exc:
        reason = str(exc)
        if reason == "invalid_code":
            raise HTTPException(status_code=404, detail="Invalid referral code")
        if reason == "self_referral":
            raise HTTPException(status_code=400, detail="Cannot claim your own referral code")
        if reason == "already_claimed":
            raise HTTPException(status_code=400, detail="Referral already claimed")
        raise HTTPException(status_code=400, detail=reason)

    credit = meta.get("referrer_credit") or {}
    trial = meta.get("trial") or {}
    return {
        "status": "claimed",
        "message": (
            "Referral claimed — Pro trial activated."
            if trial.get("granted")
            else "Referral claimed — your existing plan was kept."
        ),
        "trial": trial,
        "referrer_bonus": {
            "amount_cents": credit.get("amount_cents", 1000),
            "credited": bool(credit.get("credited")),
            "pending": bool(meta.get("reward_pending")),
            "reason": credit.get("reason"),
        },
        "code": referral_code.code,
        "referral_id": referral.id,
        "claimed_at": datetime.utcnow().isoformat(),
    }
