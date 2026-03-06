from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "JobScale"
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
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
