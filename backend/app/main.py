from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import health, jobs, users, applications

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router, prefix=f"{settings.API_V1_PREFIX}/health", tags=["Health"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["Users"])
app.include_router(jobs.router, prefix=f"{settings.API_V1_PREFIX}/jobs", tags=["Jobs"])
app.include_router(applications.router, prefix=f"{settings.API_V1_PREFIX}/applications", tags=["Applications"])


@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "version": "0.1.0", "docs": "/docs"}
