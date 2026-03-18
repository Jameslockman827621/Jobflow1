from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import health, auth, jobs, users, applications, profile, interview, billing, referrals, interview_coach, career, analytics, reviews, onboarding, cvs, auto_apply, career_report, salary_alerts

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
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["Users"])
app.include_router(jobs.router, prefix=f"{settings.API_V1_PREFIX}/jobs", tags=["Jobs"])
app.include_router(applications.router, prefix=f"{settings.API_V1_PREFIX}/applications", tags=["Applications"])
app.include_router(profile.router, prefix=f"{settings.API_V1_PREFIX}/profile", tags=["Profile"])
app.include_router(interview.router, prefix=f"{settings.API_V1_PREFIX}/interview", tags=["Interview Prep"])
app.include_router(billing.router, prefix=f"{settings.API_V1_PREFIX}/billing", tags=["Billing"])
app.include_router(referrals.router, prefix=f"{settings.API_V1_PREFIX}/referrals", tags=["Referrals"])
app.include_router(interview_coach.router, prefix=f"{settings.API_V1_PREFIX}/interview-coach", tags=["Interview Coach"])
app.include_router(onboarding.router, prefix=f"{settings.API_V1_PREFIX}/onboarding", tags=["Onboarding"])
app.include_router(career.router, prefix=f"{settings.API_V1_PREFIX}/career", tags=["Career Pathing"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_PREFIX}/analytics", tags=["Analytics"])
app.include_router(reviews.router, prefix=f"{settings.API_V1_PREFIX}/reviews", tags=["Company Reviews"])
app.include_router(auto_apply.router, prefix=f"{settings.API_V1_PREFIX}/auto-apply", tags=["Auto-Apply"])
app.include_router(career_report.router, prefix=f"{settings.API_V1_PREFIX}/reports", tags=["Career Reports"])
app.include_router(salary_alerts.router, prefix=f"{settings.API_V1_PREFIX}/alerts", tags=["Salary Alerts"])
app.include_router(cvs.router, tags=["CVs"])
app.include_router(applications.router, tags=["Applications"])


@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "version": "0.1.0", "docs": "/docs"}
