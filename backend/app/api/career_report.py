"""
Career Report API

Endpoints for generating and viewing career reports.
Free users get basic report, Pro/Premium get full report.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.api.auth import get_current_user
from app.services.career_report import CareerReportService

router = APIRouter()


@router.get("/annual")
async def get_annual_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get annual career report"""
    is_premium = current_user.subscription_plan in ("pro", "premium")
    service = CareerReportService(db)
    report = service.generate_report(current_user, period_days=365, is_premium=is_premium)
    return report


@router.get("/quarterly")
async def get_quarterly_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get quarterly career report"""
    is_premium = current_user.subscription_plan in ("pro", "premium")
    service = CareerReportService(db)
    report = service.generate_report(current_user, period_days=90, is_premium=is_premium)
    return report


@router.get("/salary-insights")
async def get_salary_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get salary market insights"""
    from app.services.salary_alerts import SalaryUpgradeService
    from app.models.profile import UserProfile
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    service = SalaryUpgradeService(db)
    insights = service.get_market_salary_insights(current_user, profile)
    
    upgrades = []
    if current_user.current_salary and profile:
        upgrades = service.find_salary_upgrades(current_user, profile)
    
    return {
        "insights": insights,
        "upgrades": upgrades[:5],
        "is_employed": current_user.is_employed,
        "current_salary": current_user.current_salary,
    }


@router.post("/set-salary")
async def set_current_salary(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set user's current salary and employment status for salary alerts"""
    salary = body.get("current_salary")
    employed = body.get("is_employed", False)
    alerts = body.get("email_alerts_enabled", True)
    frequency = body.get("alert_frequency", "daily")
    
    current_user.current_salary = salary
    current_user.is_employed = employed
    current_user.email_alerts_enabled = alerts
    current_user.alert_frequency = frequency
    
    db.commit()
    
    return {
        "message": "Salary preferences updated",
        "current_salary": current_user.current_salary,
        "is_employed": current_user.is_employed,
        "email_alerts_enabled": current_user.email_alerts_enabled,
    }
