"""
Billing API - Stripe Integration

Configure STRIPE_SECRET_KEY and STRIPE_PRICE_* env vars (Stripe Dashboard → Product → Price → API ID).
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import stripe
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user
from app.models.user import User
from app.database import SessionLocal, get_db

router = APIRouter()


class CheckoutRequest(BaseModel):
    plan: str  # "pro_monthly", "pro_yearly", "premium_monthly", "premium_yearly"
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class SubscriptionResponse(BaseModel):
    status: str
    plan: Optional[str]
    current_period_end: Optional[str]
    applications_used: int
    applications_limit: int


def _stripe_ready() -> bool:
    key = (settings.STRIPE_SECRET_KEY or "").strip()
    return bool(key) and key not in ("sk_test_placeholder",)


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user),
):
    """Create Stripe Checkout session for a subscription plan."""
    if not _stripe_ready():
        raise HTTPException(
            status_code=503,
            detail="Payments are not configured. Set STRIPE_SECRET_KEY on the server.",
        )

    price_map = settings.stripe_checkout_price_ids()
    price_id = price_map.get(request.plan)
    if not price_id:
        raise HTTPException(
            status_code=503,
            detail=f"No Stripe price ID configured for `{request.plan}`. Set the matching STRIPE_PRICE_* environment variable.",
        )

    stripe.api_key = settings.STRIPE_SECRET_KEY
    app_base = settings.APP_URL.rstrip("/")
    success_url = (request.success_url or f"{app_base}/billing/success").strip()
    cancel_url = (request.cancel_url or f"{app_base}/billing/cancel").strip()

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=cancel_url,
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
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/portal")
async def create_portal_session(
    return_url: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Stripe Customer Portal — update card, cancel subscription, etc."""
    if not _stripe_ready():
        raise HTTPException(
            status_code=503,
            detail="Payments are not configured. Set STRIPE_SECRET_KEY on the server.",
        )
    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="No Stripe customer on file yet. Complete a paid checkout first.",
        )

    stripe.api_key = settings.STRIPE_SECRET_KEY
    base = settings.APP_URL.rstrip("/")
    return_url = ((return_url or f"{base}/profile")).strip()

    try:
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=return_url,
        )
        return {"url": session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=502, detail=str(e))


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
    limit = {"free": 5, "pro": 999, "premium": 999}.get(plan, 5)

    return SubscriptionResponse(
        status=current_user.subscription_status or "active",
        plan=plan,
        current_period_end=current_user.subscription_end.isoformat() if current_user.subscription_end else None,
        applications_used=apps_count,
        applications_limit=limit,
    )


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Stripe webhook — configure STRIPE_WEBHOOK_SECRET in production."""
    payload = await request.body()
    stripe_signature = request.headers.get("Stripe-Signature", "")
    wh_secret = (settings.STRIPE_WEBHOOK_SECRET or "").strip()

    if not wh_secret or wh_secret == "whsec_placeholder":
        raise HTTPException(
            status_code=503,
            detail="Webhook endpoint not configured (STRIPE_WEBHOOK_SECRET).",
        )

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, wh_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")
        plan = session.get("metadata", {}).get("plan", "pro")
        if user_id:
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == int(user_id)).first()
                if user:
                    user.subscription_plan = plan.split("_")[0]
                    user.subscription_status = "active"
                    cid = session.get("customer")
                    if cid:
                        user.stripe_customer_id = cid
                    db.commit()
                    try:
                        from app.services.referral_rewards import try_fulfill_pending_referral_credits

                        try_fulfill_pending_referral_credits(db, user)
                    except Exception:
                        pass
            finally:
                db.close()

    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        cust_id = sub.get("customer")
        if cust_id:
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.stripe_customer_id == cust_id).first()
                if user:
                    user.subscription_plan = "free"
                    user.subscription_status = "cancelled"
                    db.commit()
            finally:
                db.close()

    elif event["type"] in (
        "customer.subscription.updated",
        "customer.subscription.created",
    ):
        sub = event["data"]["object"]
        cust_id = sub.get("customer")
        status = sub.get("status") or "active"
        # Infer plan from price nickname / metadata / product name
        plan = "pro"
        items = (sub.get("items") or {}).get("data") or []
        if items:
            price = items[0].get("price") or {}
            meta = price.get("metadata") or {}
            nickname = (price.get("nickname") or meta.get("plan") or "").lower()
            if "premium" in nickname:
                plan = "premium"
            elif "free" in nickname:
                plan = "free"
            elif "pro" in nickname:
                plan = "pro"
            # Match configured price IDs (check each ID independently)
            pid = price.get("id") or ""
            premium_ids = {
                settings.STRIPE_PRICE_PREMIUM_MONTHLY,
                settings.STRIPE_PRICE_PREMIUM_YEARLY,
            } - {None, ""}
            pro_ids = {
                settings.STRIPE_PRICE_PRO_MONTHLY,
                settings.STRIPE_PRICE_PRO_YEARLY,
            } - {None, ""}
            if pid and pid in premium_ids:
                plan = "premium"
            elif pid and pid in pro_ids:
                plan = "pro"
        if status in ("canceled", "unpaid", "incomplete_expired"):
            plan = "free"
        if cust_id:
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.stripe_customer_id == cust_id).first()
                if user:
                    user.subscription_plan = plan
                    user.subscription_status = status
                    period_end = sub.get("current_period_end")
                    if period_end:
                        from datetime import datetime

                        user.subscription_end = datetime.utcfromtimestamp(period_end)
                    db.commit()
                    # Fulfill any pending referral Stripe credits now that customer exists
                    try:
                        from app.services.referral_rewards import try_fulfill_pending_referral_credits

                        try_fulfill_pending_referral_credits(db, user)
                    except Exception:
                        pass
            finally:
                db.close()

    return {"status": "success"}


@router.get("/usage")
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get application usage stats"""
    from app.models.application import Application
    from datetime import datetime

    month_start = datetime.utcnow().replace(day=1)
    monthly_apps = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.created_at >= month_start,
    ).count()

    total_apps = db.query(Application).filter(
        Application.user_id == current_user.id,
    ).count()

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
        "plan": current_user.subscription_plan or "free",
    }
