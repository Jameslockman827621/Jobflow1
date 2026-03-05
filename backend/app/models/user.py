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
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def password(self):
        return self.hashed_password
    
    @password.setter
    def password(self, plaintext: str):
        self.hashed_password = pwd_context.hash(plaintext)
    
    def verify_password(self, plaintext: str) -> bool:
        return pwd_context.verify(plaintext, self.hashed_password)
