from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from datetime import datetime


class ReferralCode(Base, TimestampMixin):
    """User referral codes"""
    __tablename__ = "referral_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code = Column(String, unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    
    # Stats
    total_referrals = Column(Integer, default=0)
    successful_referrals = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User")
    referrals = relationship("Referral", back_populates="referrer", cascade="all, delete-orphan")


class Referral(Base, TimestampMixin):
    """Individual referral records"""
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("referral_codes.id"), nullable=False)
    referred_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    email = Column(String, nullable=False)
    
    # Status
    status = Column(String, default="pending")  # pending, registered, subscribed
    registered_at = Column(DateTime)
    subscribed_at = Column(DateTime)
    
    # Reward
    reward_given = Column(Boolean, default=False)
    reward_amount = Column(Integer, default=0)  # In cents
    
    # Relationships
    referrer = relationship("ReferralCode", back_populates="referrals")
