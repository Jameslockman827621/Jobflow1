"""
Career Report Service

Generates annual/quarterly career reports for users.
Premium upsell feature - basic report free, detailed report for Pro/Premium users.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.profile import UserProfile
from app.models.application import Application
from app.models.job import Job


class CareerReportService:
    """Generates career performance reports"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_report(self, user: User, period_days: int = 365, is_premium: bool = False) -> Dict:
        """Generate a career report for the given period"""
        cutoff = datetime.utcnow() - timedelta(days=period_days)
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        
        apps = self.db.query(Application).filter(
            Application.user_id == user.id,
            Application.created_at >= cutoff,
        ).all()
        
        report = {
            "period": f"Last {period_days} days",
            "generated_at": datetime.utcnow().isoformat(),
            "user": {"email": user.email, "name": profile.first_name if profile else "User"},
            "summary": self._build_summary(apps),
            "application_funnel": self._build_funnel(apps),
            "top_companies": self._get_top_companies(apps),
            "timeline": self._build_timeline(apps, cutoff),
            "insights": self._generate_insights(apps, user),
        }
        
        if is_premium:
            report["salary_analysis"] = self._salary_analysis(user, apps)
            report["skill_demand"] = self._skill_demand_analysis()
            report["market_position"] = self._market_position(user, profile)
            report["recommendations"] = self._career_recommendations(apps, profile)
        else:
            report["premium_teaser"] = {
                "locked_sections": ["Salary Analysis", "Skill Demand Trends", "Market Position", "AI Recommendations"],
                "upgrade_message": "Unlock your full career report with Pro or Premium",
                "upgrade_url": "/pricing",
            }
        
        return report
    
    def _build_summary(self, apps: List[Application]) -> Dict:
        total = len(apps)
        submitted = len([a for a in apps if a.status == "submitted"])
        interviews = len([a for a in apps if a.stage in ("phone_screen", "technical", "onsite")])
        offers = len([a for a in apps if a.stage == "offer"])
        
        return {
            "total_applications": total,
            "submitted": submitted,
            "interview_rate": round((interviews / total * 100), 1) if total > 0 else 0,
            "offer_rate": round((offers / total * 100), 1) if total > 0 else 0,
            "interviews": interviews,
            "offers": offers,
            "response_rate": round(((interviews + offers) / submitted * 100), 1) if submitted > 0 else 0,
        }
    
    def _build_funnel(self, apps: List[Application]) -> List[Dict]:
        stages = [
            ("Applied", len(apps)),
            ("Responded", len([a for a in apps if a.stage != "not_started"])),
            ("Phone Screen", len([a for a in apps if a.stage in ("phone_screen", "technical", "onsite", "offer")])),
            ("Technical", len([a for a in apps if a.stage in ("technical", "onsite", "offer")])),
            ("Onsite", len([a for a in apps if a.stage in ("onsite", "offer")])),
            ("Offer", len([a for a in apps if a.stage == "offer"])),
        ]
        total = stages[0][1] or 1
        return [{"stage": name, "count": count, "pct": round(count / total * 100)} for name, count in stages]
    
    def _get_top_companies(self, apps: List[Application]) -> List[Dict]:
        company_counts = {}
        for app in apps:
            job = self.db.query(Job).filter(Job.id == app.job_id).first()
            if job:
                company_counts[job.company] = company_counts.get(job.company, 0) + 1
        
        sorted_companies = sorted(company_counts.items(), key=lambda x: -x[1])
        return [{"company": name, "applications": count} for name, count in sorted_companies[:10]]
    
    def _build_timeline(self, apps: List[Application], cutoff: datetime) -> List[Dict]:
        monthly = {}
        for app in apps:
            month_key = app.created_at.strftime("%Y-%m") if app.created_at else "unknown"
            if month_key not in monthly:
                monthly[month_key] = {"month": month_key, "applications": 0, "interviews": 0, "offers": 0}
            monthly[month_key]["applications"] += 1
            if app.stage in ("phone_screen", "technical", "onsite", "offer"):
                monthly[month_key]["interviews"] += 1
            if app.stage == "offer":
                monthly[month_key]["offers"] += 1
        
        return sorted(monthly.values(), key=lambda x: x["month"])
    
    def _generate_insights(self, apps: List[Application], user: User) -> List[Dict]:
        insights = []
        total = len(apps)
        
        if total == 0:
            insights.append({
                "type": "action", "icon": "🎯",
                "title": "Start Your Journey",
                "description": "You haven't applied to any jobs yet. Complete your profile and start applying!",
            })
            return insights
        
        interviews = len([a for a in apps if a.stage in ("phone_screen", "technical", "onsite", "offer")])
        rate = (interviews / total * 100) if total > 0 else 0
        
        if rate >= 20:
            insights.append({"type": "positive", "icon": "🔥", "title": "Strong Interview Rate",
                "description": f"Your {rate:.0f}% interview rate is above average. Your applications are resonating with employers."})
        elif rate >= 10:
            insights.append({"type": "neutral", "icon": "📊", "title": "Solid Progress",
                "description": f"Your {rate:.0f}% interview rate is on track. Consider tailoring your CV more specifically to each role."})
        else:
            insights.append({"type": "action", "icon": "💡", "title": "Boost Your Response Rate",
                "description": "Try tailoring your CV for each application and adding a cover letter."})
        
        if total >= 10:
            insights.append({"type": "positive", "icon": "💪", "title": "Consistent Effort",
                "description": f"You've sent {total} applications. Consistency is key to landing the right role."})
        
        if user.is_employed and user.current_salary:
            insights.append({"type": "info", "icon": "💰", "title": "Salary Growth Opportunity",
                "description": "As an employed professional, you're in a strong negotiation position. We're monitoring higher-paying roles for you."})
        
        return insights
    
    def _salary_analysis(self, user: User, apps: List[Application]) -> Dict:
        jobs_with_salary = []
        for app in apps:
            job = self.db.query(Job).filter(Job.id == app.job_id).first()
            if job and job.max_salary:
                jobs_with_salary.append(job.max_salary)
        
        if not jobs_with_salary:
            return {"available": False, "message": "No salary data available for applied jobs"}
        
        return {
            "available": True,
            "avg_applied_salary": sum(jobs_with_salary) // len(jobs_with_salary),
            "max_applied_salary": max(jobs_with_salary),
            "min_applied_salary": min(jobs_with_salary),
            "current_salary": user.current_salary,
            "potential_increase": max(jobs_with_salary) - (user.current_salary or 0) if user.current_salary else None,
        }
    
    def _skill_demand_analysis(self) -> List[Dict]:
        jobs = self.db.query(Job).filter(Job.is_active == True).limit(200).all()
        skill_counts = {}
        for job in jobs:
            if job.skills_required:
                for skill in job.skills_required:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        sorted_skills = sorted(skill_counts.items(), key=lambda x: -x[1])
        return [{"skill": name, "demand": count} for name, count in sorted_skills[:15]]
    
    def _market_position(self, user: User, profile: Optional[UserProfile]) -> Dict:
        total_jobs = self.db.query(Job).filter(Job.is_active == True).count()
        if user.current_salary:
            higher_paying = self.db.query(Job).filter(
                Job.is_active == True, Job.max_salary != None, Job.max_salary > user.current_salary
            ).count()
        else:
            higher_paying = 0
        
        return {
            "total_active_jobs": total_jobs,
            "higher_paying_jobs": higher_paying,
            "your_salary_percentile": None,
        }
    
    def _career_recommendations(self, apps: List[Application], profile: Optional[UserProfile]) -> List[str]:
        recs = []
        total = len(apps)
        interviews = len([a for a in apps if a.stage in ("phone_screen", "technical", "onsite", "offer")])
        
        if total > 0 and interviews == 0:
            recs.append("Consider getting your CV professionally reviewed")
            recs.append("Target companies where your skills are a strong match")
        if total < 5:
            recs.append("Apply to more roles - aim for at least 10-15 per week")
        
        recs.append("Keep your LinkedIn profile updated and active")
        recs.append("Build in public - share projects and learnings")
        recs.append("Network with people in your target companies")
        
        return recs
