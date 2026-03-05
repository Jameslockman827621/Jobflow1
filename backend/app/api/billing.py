"""
Billing API - Stripe Integration

Plans:
- Free: 5 applications/month
- Pro ($29/mo): Unlimited applications, priority AI, analytics
- Premium ($79/mo): Everything + interview coach, resume review

Endpoints:
- POST /billing/checkout - Create checkout session
- POST /billing/portal - Create portal session
- POST /billing/webhook - Stripe webhook handler
- GET /billing/subscription - Get current subscription
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict
import stripe
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user
from app.models.user import User
from app.database import SessionLocal

router = APIRouter()

# Stripe setup (use environment variable in production)
stripe.api_key = settings.OPENAI_API_KEY  # TODO: Add STRIPE_SECRET_KEY to config

# Plan IDs (replace with actual Stripe product IDs)
PLAN_IDS = {
    "pro_monthly": "price_pro_monthly",
    "pro_yearly": "price_pro_yearly",
    "premium_monthly": "price_premium_monthly",
    "premium_yearly": "price_premium_yearly",
}


class CheckoutRequest(BaseModel):
    plan: str  # "pro_monthly", "pro_yearly", etc.
    success_url: str = "http://localhost:3000/billing/success"
    cancel_url: str = "http://localhost:3000/billing/cancel"


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class SubscriptionResponse(BaseModel):
    status: str  # "active", "cancelled", "none"
    plan: Optional[str]
    current_period_end: Optional[str]
    applications_used: int
    applications_limit: int


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user),
):
    """Create Stripe checkout session"""
    if request.plan not in PLAN_IDS:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": PLAN_IDS[request.plan],
                "quantity": 1,
            }],
            mode="subscription",
            success_url=f"{request.success_url}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=request.cancel_url,
            metadata={
                "user_id": str(current_user.id),
                "plan": request.plan,
            },
            customer_email=current_user.email,
        )
        
        return CheckoutResponse(
            checkout_url=session.url,
            session_id=session.id,
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portal")
async def create_portal_session(
    current_user: User = Depends(get_current_user),
):
    """Create Stripe customer portal session for subscription management"""
    # In production, get customer_id from database
    # For now, this is a placeholder
    raise HTTPException(status_code=501, detail="Portal not configured - add customer_id to user model")


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(lambda: SessionLocal()),
):
    """Get current user's subscription status"""
    # In production, fetch from Stripe using customer_id
    # For now, return free tier
    
    # Count applications this month
    from app.models.application import Application
    from datetime import datetime
    
    month_start = datetime.utcnow().replace(day=1)
    apps_count = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.created_at >= month_start,
    ).count()
    
    return SubscriptionResponse(
        status="active",  # Would check Stripe in production
        plan="free",
        current_period_end=None,
        applications_used=apps_count,
        applications_limit=5,  # Free tier limit
    )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str,
):
    """Handle Stripe webhooks"""
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.OPENAI_API_KEY  # TODO: Use webhook secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle events
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        # Activate subscription for user
        user_id = session.get("metadata", {}).get("user_id")
        # TODO: Update user's subscription in database
    
    elif event["type"] == "customer.subscription.deleted":
        # Downgrade to free tier
        pass
    
    return {"status": "success"}


@router.get("/usage")
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(lambda: SessionLocal()),
):
    """Get application usage stats"""
    from app.models.application import Application
    from datetime import datetime, timedelta
    
    # This month
    month_start = datetime.utcnow().replace(day=1)
    monthly_apps = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.created_at >= month_start,
    ).count()
    
    # All time
    total_apps = db.query(Application).filter(
        Application.user_id == current_user.id,
    ).count()
    
    # Interview rate
    interviews = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.stage.in_(["phone_screen", "technical", "onsite"]),
    ).count()
    
    interview_rate = round((interviews / total_apps * 100), 1) if total_apps > 0 else 0
    
    return {
        "monthly_applications": monthly_apps,
        "total_applications": total_apps,
        "interviews": interviews,
        "interview_rate": f"{interview_rate}%",
        "plan": "free",  # Would check subscription in production
    }
