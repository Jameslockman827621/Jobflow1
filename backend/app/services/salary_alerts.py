"""
Salary Upgrade Alert Service

Finds better-paying jobs for employed users and sends them notifications.
Key feature of the "always searching for better" post-hire retention strategy.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.models.profile import UserProfile
from app.models.job import Job
from app.models.application import Application
from app.services.matching import JobMatcher
from app.services.email import email_service
from app.core.config import settings
from app.tasks import celery_app


class SalaryUpgradeService:
    """Finds better-paying opportunities for employed users"""
    
    def __init__(self, db: Session):
        self.db = db
        self.matcher = JobMatcher(db)
    
    def find_salary_upgrades(self, user: User, profile: UserProfile, min_increase_pct: float = 10.0) -> List[Dict]:
        """Find jobs that pay more than user's current salary"""
        if not user.current_salary or user.current_salary <= 0:
            return []
        
        min_target = int(user.current_salary * (1 + min_increase_pct / 100))
        
        jobs = self.db.query(Job).filter(
            Job.is_active == True,
            Job.max_salary != None,
            Job.max_salary >= min_target,
        ).order_by(Job.max_salary.desc()).limit(100).all()
        
        upgrades = []
        for job in jobs:
            score = self.matcher.calculate_match_score(profile, job)
            if score >= 50:
                increase = job.max_salary - user.current_salary
                increase_pct = round((increase / user.current_salary) * 100)
                upgrades.append({
                    "job_id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "url": job.external_url,
                    "salary": job.max_salary,
                    "increase": increase,
                    "increase_pct": increase_pct,
                    "match_score": score,
                })
        
        upgrades.sort(key=lambda x: (-x["increase_pct"], -x["match_score"]))
        return upgrades[:10]
    
    def get_market_salary_insights(self, user: User, profile: UserProfile) -> Dict:
        """Get salary market insights for user's role"""
        if not profile:
            return {}
        
        roles = []
        if hasattr(profile, 'desired_roles') and profile.desired_roles:
            roles = profile.desired_roles
        
        jobs = self.db.query(Job).filter(
            Job.is_active == True,
            Job.max_salary != None,
        ).limit(500).all()
        
        if not jobs:
            return {"avg_salary": 0, "median_salary": 0, "top_10_pct": 0, "total_jobs": 0}
        
        salaries = sorted([j.max_salary for j in jobs if j.max_salary])
        if not salaries:
            return {"avg_salary": 0, "median_salary": 0, "top_10_pct": 0, "total_jobs": 0}
        
        avg = sum(salaries) // len(salaries)
        median = salaries[len(salaries) // 2]
        top_10 = salaries[int(len(salaries) * 0.9)] if len(salaries) >= 10 else salaries[-1]
        
        return {
            "avg_salary": avg,
            "median_salary": median,
            "top_10_pct": top_10,
            "total_jobs": len(salaries),
            "your_salary": user.current_salary,
            "percentile": _calc_percentile(salaries, user.current_salary) if user.current_salary else None,
        }


def _calc_percentile(sorted_salaries: List[int], salary: int) -> int:
    """Calculate what percentile a salary falls in"""
    below = sum(1 for s in sorted_salaries if s < salary)
    return round((below / len(sorted_salaries)) * 100)


def send_salary_upgrade_email(user: User, upgrades: List[Dict]) -> bool:
    """Send salary upgrade alert email"""
    if not upgrades:
        return False
    
    jobs_html = ""
    for job in upgrades[:5]:
        salary_str = f"£{job['salary']:,}"
        increase_str = f"+£{job['increase']:,} ({job['increase_pct']}% more)"
        jobs_html += f"""
        <div style="border: 1px solid #e5e7eb; padding: 15px; border-radius: 8px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <p style="font-weight: bold; margin: 0 0 4px 0; font-size: 16px;">{job['title']}</p>
                    <p style="color: #666; margin: 0 0 4px 0;">{job['company']} • {job['location']}</p>
                </div>
                <div style="text-align: right;">
                    <p style="font-weight: bold; color: #16a34a; margin: 0; font-size: 16px;">{salary_str}</p>
                    <p style="color: #16a34a; margin: 0; font-size: 13px;">{increase_str}</p>
                </div>
            </div>
            <p style="margin: 8px 0 0 0;">
                <a href="{job['url']}" style="color: #2563eb; font-size: 14px;">View Job →</a>
                <span style="color: #999; font-size: 12px; margin-left: 12px;">{job['match_score']}% match</span>
            </p>
        </div>
        """
    
    top_increase = upgrades[0]['increase_pct']
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="background: linear-gradient(135deg, #059669, #10b981); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">💰 Salary Upgrade Alert</h1>
            <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0;">We found jobs paying up to {top_increase}% more than your current salary</p>
        </div>
        
        <div style="padding: 30px; background: #f9fafb; border-radius: 0 0 12px 12px;">
            <h3 style="margin-top: 0;">Top Opportunities:</h3>
            {jobs_html}
            
            <div style="background: #eff6ff; border: 1px solid #bfdbfe; padding: 15px; border-radius: 8px; margin-top: 20px;">
                <p style="margin: 0; font-size: 14px; color: #1e40af;">
                    <strong>💡 Pro Tip:</strong> The best time to negotiate is when you already have a job.
                    These opportunities were hand-picked based on your skills and experience.
                </p>
            </div>
            
            <p style="text-align: center; margin-top: 25px;">
                <a href="{settings.APP_URL}/dashboard" 
                   style="background-color: #059669; color: white; padding: 14px 28px; 
                          text-decoration: none; border-radius: 8px; display: inline-block; font-weight: bold;">
                    View All Opportunities
                </a>
            </p>
            
            <hr style="margin: 25px 0; border: none; border-top: 1px solid #e5e7eb;" />
            
            <p style="color: #666; font-size: 12px; text-align: center;">
                You're receiving this because you have salary alerts enabled.
                <a href="{settings.APP_URL}/profile" style="color: #666;">Manage alert preferences</a>
            </p>
        </div>
    </body>
    </html>
    """
    
    return email_service.send_email(
        user.email,
        f"💰 Jobs paying {top_increase}%+ more than your current salary",
        html
    )


@celery_app.task
def run_salary_upgrade_alerts():
    """Celery task: find and send salary upgrade alerts to employed users"""
    db = SessionLocal()
    try:
        users = db.query(User).filter(
            User.is_active == True,
            User.is_employed == True,
            User.email_alerts_enabled == True,
            User.current_salary != None,
        ).all()
        
        alerts_sent = 0
        service = SalaryUpgradeService(db)
        
        for user in users:
            profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
            if not profile:
                continue
            
            upgrades = service.find_salary_upgrades(user, profile)
            if upgrades:
                send_salary_upgrade_email(user, upgrades)
                alerts_sent += 1
        
        return {"status": "completed", "alerts_sent": alerts_sent}
    finally:
        db.close()
