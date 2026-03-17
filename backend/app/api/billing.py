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
from app.database import SessionLocal, get_db

router = APIRouter()

# Stripe setup (use environment variable in production)
stripe.api_key = settings.STRIPE_SECRET_KEY or "sk_test_placeholder"

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
    db: Session = Depends(get_db),
):
    """Get current user's subscription status"""
    from app.models.application import Application
    from datetime import datetime
    
    month_start = datetime.utcnow().replace(day=1)
    apps_count = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.created_at >= month_start,
    ).count()
    
    plan = current_user.subscription_plan or "free"
    applications_limit = 5 if plan == "free" else 999999
    
    return SubscriptionResponse(
        status="active",
        plan=plan,
        current_period_end=None,
        applications_used=apps_count,
        applications_limit=applications_limit,
    )


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    payload = await request.body()
    stripe_signature = request.headers.get("Stripe-Signature", "")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET or "whsec_placeholder"
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle events
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")
        plan = session.get("metadata", {}).get("plan", "pro")
        if user_id:
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == int(user_id)).first()
                if user:
                    user.subscription_plan = plan.split("_")[0]  # "pro_monthly" -> "pro"
                    user.subscription_status = "active"
                    user.stripe_customer_id = session.get("customer")
                    db.commit()
            finally:
                db.close()
    
    elif event["type"] == "customer.subscription.deleted":
        # Downgrade to free tier
        pass
    
    return {"status": "success"}


@router.get("/usage")
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
