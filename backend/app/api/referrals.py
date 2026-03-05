"""
Referral System API

Users get:
- $10 credit for each friend who signs up
- $50 credit for each friend who subscribes to Pro
- Friends get 1 month free Pro

Endpoints:
- GET /referrals/code - Get user's referral code
- POST /referrals/invite - Send invite to friend
- GET /referrals/stats - Get referral stats
- POST /referrals/claim - Claim referral (new user)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from sqlalchemy.orm import Session
import secrets
import string

from app.database import SessionLocal
from app.core.security import get_current_user
from app.models.user import User
from app.models.referral import ReferralCode, Referral
from app.services.email import email_service

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
        # Create new referral code
        code = generate_referral_code()
        referral_code = ReferralCode(
            user_id=current_user.id,
            code=code,
        )
        db.add(referral_code)
        db.commit()
        db.refresh(referral_code)
    
    return ReferralCodeResponse(
        code=referral_code.code,
        link=f"http://localhost:3000/signup?ref={referral_code.code}",
        total_referrals=referral_code.total_referrals,
        successful_referrals=referral_code.successful_referrals,
        earnings=referral_code.successful_referrals * 10,  # $10 per signup
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
    
    # Check if email already referred
    existing = db.query(Referral).filter(
        Referral.referrer_id == referral_code.id,
        Referral.email == request.email,
    ).first()
    
    if existing:
        return {"status": "already_sent", "message": "Invite already sent to this email"}
    
    # Create referral record
    referral = Referral(
        referrer_id=referral_code.id,
        email=request.email,
        status="pending",
    )
    db.add(referral)
    
    # Send invite email
    invite_link = f"http://localhost:3000/signup?ref={referral_code.code}"
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>You've been invited to JobScale! 🚀</h2>
        
        <p>{current_user.email} thinks you'd love JobScale - the AI-powered job search tool.</p>
        
        <div style="background: #eff6ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0 0 15px 0;"><strong>Your benefits:</strong></p>
            <ul style="margin: 0;">
                <li>1 month free Pro plan ($29 value)</li>
                <li>Unlimited AI applications</li>
                <li>Priority CV tailoring</li>
                <li>Interview prep tools</li>
            </ul>
        </div>
        
        <p style="margin-top: 20px;">
            <a href="{invite_link}" 
               style="background-color: #2563eb; color: white; padding: 12px 24px; 
                      text-decoration: none; border-radius: 6px; display: inline-block;">
                Claim Your Free Month
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
    
    email_service.send_email(request.email, "You're invited to try JobScale! 🎁", html)
    
    db.commit()
    
    return {"status": "sent", "message": f"Invite sent to {request.email}"}


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
        total_referrals=referral_code.total_referrals,
        pending=len([r for r in referrals if r.status == "pending"]),
        registered=len([r for r in referrals if r.status == "registered"]),
        subscribed=len([r for r in referrals if r.status == "subscribed"]),
        total_earnings=referral_code.successful_referrals * 10,
        referrals=[
            {
                "email": r.email,
                "status": r.status,
                "registered_at": r.registered_at.isoformat() if r.registered_at else None,
                "reward": "$10" if r.status == "registered" else "$50" if r.status == "subscribed" else "$0",
            }
            for r in referrals
        ],
    )


@router.post("/claim")
async def claim_referral(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Claim a referral code (new user)"""
    referral_code = db.query(ReferralCode).filter(
        ReferralCode.code == code,
        ReferralCode.is_active == True,
    ).first()
    
    if not referral_code:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    
    # Check if already claimed
    existing = db.query(Referral).filter(
        Referral.referred_user_id == current_user.id,
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Referral already claimed")
    
    # Update referral record
    referral = db.query(Referral).filter(
        Referral.referrer_id == referral_code.id,
        Referral.email == current_user.email,
    ).first()
    
    if referral:
        referral.status = "registered"
        referral.registered_at = db.query(func.now()).scalar()
        referral.referred_user_id = current_user.id
        
        # Update referrer stats
        referral_code.total_referrals += 1
        referral_code.successful_referrals += 1
    
    db.commit()
    
    return {
        "status": "claimed",
        "message": "Referral claimed! You get 1 month free Pro.",
        "referrer_bonus": "$10 credited to your friend",
    }


# Import func for the claim endpoint
from sqlalchemy import func
