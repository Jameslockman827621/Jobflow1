from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from passlib.context import CryptContext

from app.models.base import Base, TimestampMixin

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    stripe_customer_id = Column(String, nullable=True)
    subscription_plan = Column(String, default="free")
    subscription_status = Column(String, default="active")
    subscription_end = Column(DateTime, nullable=True)
    email_alerts_enabled = Column(Boolean, default=True)
    alert_frequency = Column(String, default="daily")
    current_salary = Column(Integer, nullable=True)
    is_employed = Column(Boolean, default=False)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    cvs = relationship("CV", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def password(self):
        return self.hashed_password
    
    @password.setter
    def password(self, plaintext: str):
        self.hashed_password = pwd_context.hash(plaintext)
    
    def verify_password(self, plaintext: str) -> bool:
        return pwd_context.verify(plaintext, self.hashed_password)
