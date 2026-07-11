from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List, Optional, Union


class Settings(BaseSettings):
    # App
    APP_NAME: str = "JobScale"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/jobscale"
    DATABASE_ASYNC_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/jobscale"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Auth
    SECRET_KEY: str = "change-me-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI/LLM
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4-turbo-preview"
    
    # Scraping
    PROXY_POOL: Optional[List[str]] = None
    REQUEST_DELAY_MS: int = 1000
    APIFY_API_KEY: Optional[str] = None
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: str = "noreply@jobscale.local"
    SENDGRID_API_KEY: Optional[str] = None
    
    # Stripe (set price IDs from Stripe Dashboard → Products → Price API IDs)
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRICE_PRO_MONTHLY: Optional[str] = None
    STRIPE_PRICE_PRO_YEARLY: Optional[str] = None
    STRIPE_PRICE_PREMIUM_MONTHLY: Optional[str] = None
    STRIPE_PRICE_PREMIUM_YEARLY: Optional[str] = None
    
    # App URLs
    APP_URL: str = "http://localhost:3000"
    
    # CORS — comma-separated origins in env, e.g. "https://app.example.com,http://localhost:3000"
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000"

    # When no scrapers return jobs, return an honest empty result (disabled by default).
    # The aggregator now runs runtime ATS discovery for any company name, so users
    # can search any company on a supported ATS without needing demo data.
    AUTO_SEED_DEMO_JOBS: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if v is None:
            return ["http://localhost:3000"]
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            parts = [s.strip() for s in v.split(",") if s.strip()]
            return parts if parts else ["http://localhost:3000"]
        return v

    def cors_origins(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [self.CORS_ORIGINS]

    def stripe_checkout_price_ids(self) -> dict:
        m = {}
        if self.STRIPE_PRICE_PRO_MONTHLY:
            m["pro_monthly"] = self.STRIPE_PRICE_PRO_MONTHLY
        if self.STRIPE_PRICE_PRO_YEARLY:
            m["pro_yearly"] = self.STRIPE_PRICE_PRO_YEARLY
        if self.STRIPE_PRICE_PREMIUM_MONTHLY:
            m["premium_monthly"] = self.STRIPE_PRICE_PREMIUM_MONTHLY
        if self.STRIPE_PRICE_PREMIUM_YEARLY:
            m["premium_yearly"] = self.STRIPE_PRICE_PREMIUM_YEARLY
        return m

    def assert_safe_for_production(self) -> None:
        if self.ENVIRONMENT.lower() != "production":
            return
        problems = []
        weak = "change-me" in self.SECRET_KEY.lower() or len(self.SECRET_KEY) < 32
        if weak:
            problems.append("SECRET_KEY must be 32+ chars and not the default")
        if self.DEBUG:
            problems.append("DEBUG must be false in production")
        if self.AUTO_SEED_DEMO_JOBS:
            problems.append("AUTO_SEED_DEMO_JOBS must be false in production (would show fake jobs)")
        if "postgres:postgres" in self.DATABASE_URL:
            problems.append("DATABASE_URL must not use the default postgres:postgres credentials")
        if problems:
            raise RuntimeError(
                "ENVIRONMENT=production requires safe config:\n  - " +
                "\n  - ".join(problems)
            )


settings = Settings()
