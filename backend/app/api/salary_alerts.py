"""
Salary Alerts & Career Reports API

Endpoints for the post-hire retention flow:
- Salary upgrade alerts
- Career reports (annual review)
- Alert preferences
- Employment status tracking
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.profile import UserProfile
from app.models.application import Application
from app.api.auth import get_current_user
from app.services.salary_alerts import SalaryAlertService
from app.services.email import email_service

router = APIRouter()


@router.get("/upgrades")
async def get_salary_upgrades(
    min_increase: float = 10.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get jobs that pay more than your current salary"""
    service = SalaryAlertService(db)
    upgrades = service.find_salary_upgrades(current_user, min_increase_pct=min_increase)
    return {
        "upgrades": upgrades,
        "total": len(upgrades),
        "current_salary": current_user.current_salary,
        "min_increase_pct": min_increase,
    }


@router.get("/report")
async def get_career_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get annual career & salary report"""
    service = SalaryAlertService(db)
    report = service.generate_salary_report(current_user)

    apps = db.query(Application).filter(Application.user_id == current_user.id).all()
    total_apps = len(apps)
    interviews = len([a for a in apps if a.stage in ("phone_screen", "technical", "onsite")])
    offers = len([a for a in apps if a.stage == "offer"])

    report["career_stats"] = {
        "total_applications": total_apps,
        "interviews": interviews,
        "offers": offers,
        "interview_rate": round(interviews / total_apps * 100, 1) if total_apps > 0 else 0,
        "offer_rate": round(offers / total_apps * 100, 1) if total_apps > 0 else 0,
    }

    report["subscription"] = {
        "plan": current_user.subscription_plan or "free",
        "is_premium": current_user.subscription_plan in ("pro", "premium"),
        "upgrade_benefits": [] if current_user.subscription_plan != "free" else [
            "Unlimited applications (free plan: 5/month)",
            "Priority AI CV tailoring",
            "Salary upgrade alerts",
            "Weekly career reports",
            "Interview coaching",
        ],
    }

    return report


@router.post("/employment")
async def update_employment_status(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update employment status and current salary for upgrade tracking"""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if "is_employed" in body:
        user.is_employed = body["is_employed"]
    if "current_salary" in body:
        user.current_salary = body["current_salary"]
    db.commit()
    db.refresh(user)
    return {
        "is_employed": user.is_employed,
        "current_salary": user.current_salary,
        "message": "Employment status updated. We'll find you better-paying opportunities!",
    }


@router.get("/preferences")
async def get_alert_preferences(
    current_user: User = Depends(get_current_user),
):
    """Get email alert preferences"""
    return {
        "email_alerts_enabled": current_user.email_alerts_enabled,
        "alert_frequency": current_user.alert_frequency,
        "current_salary": current_user.current_salary,
        "is_employed": current_user.is_employed,
    }


@router.put("/preferences")
async def update_alert_preferences(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update email alert preferences"""
    user = db.query(User).filter(User.id == current_user.id).first()
    if "email_alerts_enabled" in body:
        user.email_alerts_enabled = body["email_alerts_enabled"]
    if "alert_frequency" in body:
        if body["alert_frequency"] in ("daily", "weekly", "off"):
            user.alert_frequency = body["alert_frequency"]
    db.commit()
    return {
        "email_alerts_enabled": user.email_alerts_enabled,
        "alert_frequency": current_user.alert_frequency,
    }


@router.post("/send-test-alert")
async def send_test_alert(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a test salary upgrade alert email"""
    service = SalaryAlertService(db)
    upgrades = service.find_salary_upgrades(current_user, min_increase_pct=5.0)

    jobs_for_email = []
    for u in upgrades[:5]:
        jobs_for_email.append({
            "title": f"{u['title']} (+£{u['salary_increase']:,})",
            "company": u["company"],
            "location": u.get("location", ""),
            "url": u.get("external_url", "#"),
        })

    if not jobs_for_email:
        jobs_for_email = [{
            "title": "Senior Software Engineer (+£15,000)",
            "company": "Example Corp",
            "location": "London, UK",
            "url": "#",
        }]

    email_service.send_job_alert(current_user.email, jobs_for_email)
    return {"message": "Test alert sent! Check your email (or console in dev mode)."}
