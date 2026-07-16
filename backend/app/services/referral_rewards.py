"""Referral rewards — grant real Pro trial + optional Stripe customer credit."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.referral import Referral, ReferralCode
from app.models.user import User

logger = logging.getLogger(__name__)

REFERRAL_PRO_DAYS = 30
REFERRER_CREDIT_CENTS = 1000  # $10 display / Stripe balance when possible


def grant_referee_pro_trial(user: User, days: int = REFERRAL_PRO_DAYS) -> dict:
    """Give the referred user a real time-boxed Pro plan (DB truth, not marketing copy)."""
    end = datetime.utcnow() + timedelta(days=days)
    # Don't downgrade an existing paid plan
    current = (user.subscription_plan or "free").lower()
    if current in ("pro", "premium") and user.subscription_status == "active":
        # Extend end if already paid
        if user.subscription_end and user.subscription_end > end:
            return {
                "plan": user.subscription_plan,
                "subscription_end": user.subscription_end.isoformat(),
                "granted": False,
                "reason": "already_paid",
            }
    user.subscription_plan = "pro"
    user.subscription_status = "active"
    user.subscription_end = end
    return {
        "plan": "pro",
        "subscription_end": end.isoformat(),
        "granted": True,
        "days": days,
    }


def credit_referrer_stripe(referrer_user: User, amount_cents: int = REFERRER_CREDIT_CENTS) -> dict:
    """
    Apply a real Stripe customer balance credit when Stripe + customer exist.

    Returns status dict; never pretends success without Stripe confirmation.
    """
    key = (settings.STRIPE_SECRET_KEY or "").strip()
    if not key or key.lower() in ("mock", "placeholder", "sk_test_placeholder"):
        return {"credited": False, "reason": "stripe_not_configured", "amount_cents": amount_cents}
    if not referrer_user.stripe_customer_id:
        return {"credited": False, "reason": "no_stripe_customer", "amount_cents": amount_cents}
    try:
        import stripe

        stripe.api_key = key
        # Negative amount = credit to customer balance
        tx = stripe.Customer.create_balance_transaction(
            referrer_user.stripe_customer_id,
            amount=-abs(amount_cents),
            currency="usd",
            description="JobScale referral reward",
        )
        return {
            "credited": True,
            "amount_cents": amount_cents,
            "balance_transaction_id": getattr(tx, "id", None) or (tx.get("id") if isinstance(tx, dict) else None),
        }
    except Exception as exc:
        logger.warning("Stripe referral credit failed: %s", exc)
        return {"credited": False, "reason": str(exc)[:200], "amount_cents": amount_cents}


def apply_referral_claim(
    db: Session,
    *,
    code: str,
    claimant: User,
) -> Tuple[Referral, ReferralCode, dict]:
    """
    Claim a referral code for ``claimant``.

    Side effects:
    - Creates/updates Referral row
    - Grants claimant Pro trial
    - Attempts Stripe credit for referrer; sets reward_given when credit lands OR
      when we record a pending account credit (reward_amount set either way)
    """
    referral_code = (
        db.query(ReferralCode)
        .filter(ReferralCode.code == code, ReferralCode.is_active == True)  # noqa: E712
        .first()
    )
    if not referral_code:
        raise ValueError("invalid_code")

    if referral_code.user_id == claimant.id:
        raise ValueError("self_referral")

    # Re-bind claimant into this session (auth dependency may use a different Session)
    claimant_db = db.query(User).filter(User.id == claimant.id).first()
    if not claimant_db:
        raise ValueError("invalid_user")
    claimant = claimant_db

    existing = (
        db.query(Referral).filter(Referral.referred_user_id == claimant.id).first()
    )
    if existing:
        raise ValueError("already_claimed")

    referral = (
        db.query(Referral)
        .filter(
            Referral.referrer_id == referral_code.id,
            Referral.email == claimant.email,
        )
        .first()
    )
    if not referral:
        referral = Referral(
            referrer_id=referral_code.id,
            email=claimant.email,
            status="pending",
        )
        db.add(referral)
        db.flush()

    referral.status = "registered"
    referral.registered_at = datetime.utcnow()
    referral.referred_user_id = claimant.id
    referral.reward_amount = REFERRER_CREDIT_CENTS

    referral_code.total_referrals = (referral_code.total_referrals or 0) + 1
    referral_code.successful_referrals = (referral_code.successful_referrals or 0) + 1

    trial = grant_referee_pro_trial(claimant)

    referrer_user = db.query(User).filter(User.id == referral_code.user_id).first()
    stripe_result = {"credited": False, "reason": "no_referrer"}
    if referrer_user:
        stripe_result = credit_referrer_stripe(referrer_user)
        if stripe_result.get("credited"):
            referral.reward_given = True
        else:
            # Honest: credit pending until referrer has a Stripe customer (after checkout)
            referral.reward_given = False

    db.commit()
    db.refresh(referral)
    db.refresh(claimant)

    return referral, referral_code, {
        "trial": trial,
        "referrer_credit": stripe_result,
        "reward_pending": not bool(referral.reward_given),
    }


def try_fulfill_pending_referral_credits(db: Session, user: User) -> int:
    """
    After a referrer completes Stripe checkout, fulfill pending referral credits.
    Returns number of credits applied.
    """
    codes = db.query(ReferralCode).filter(ReferralCode.user_id == user.id).all()
    if not codes:
        return 0
    code_ids = [c.id for c in codes]
    pending = (
        db.query(Referral)
        .filter(
            Referral.referrer_id.in_(code_ids),
            Referral.reward_given == False,  # noqa: E712
            Referral.reward_amount > 0,
            Referral.status.in_(("registered", "subscribed")),
        )
        .all()
    )
    applied = 0
    for row in pending:
        result = credit_referrer_stripe(user, row.reward_amount or REFERRER_CREDIT_CENTS)
        if result.get("credited"):
            row.reward_given = True
            applied += 1
    if applied:
        db.commit()
    return applied
