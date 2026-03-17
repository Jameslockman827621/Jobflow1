"""
Salary Upgrade Alert Service

Finds better-paying jobs for currently employed users.
The core post-hire retention feature of JobScale.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.profile import UserProfile
from app.models.job import Job
from app.models.preferences import UserPreferences
from app.services.matching import JobMatcher


class SalaryAlertService:
    def __init__(self, db: Session):
        self.db = db
        self.matcher = JobMatcher(db)

    def find_salary_upgrades(self, user: User, min_increase_pct: float = 10.0) -> List[Dict]:
        """Find jobs that pay more than user's current salary"""
        if not user.current_salary:
            return []

        target_salary = int(user.current_salary * (1 + min_increase_pct / 100))

        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        preferences = self.db.query(UserPreferences).filter(
            UserPreferences.user_id == user.id, UserPreferences.is_active == True
        ).first()

        query = self.db.query(Job).filter(Job.is_active == True)

        if preferences and preferences.target_roles:
            role_filters = []
            for role in preferences.target_roles:
                role_filters.append(Job.title.ilike(f"%{role}%"))
            if role_filters:
                from sqlalchemy import or_
                query = query.filter(or_(*role_filters))

        query = query.filter(
            ((Job.min_salary != None) & (Job.min_salary >= target_salary)) |
            ((Job.max_salary != None) & (Job.max_salary >= target_salary))
        )

        jobs = query.order_by(Job.max_salary.desc().nullslast()).limit(20).all()

        upgrades = []
        for job in jobs:
            job_salary = job.max_salary or job.min_salary or 0
            increase = job_salary - user.current_salary
            increase_pct = round((increase / user.current_salary) * 100, 1) if user.current_salary > 0 else 0

            match_score = 0
            if profile:
                match_score = self.matcher.calculate_match_score(profile, job)

            upgrades.append({
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "salary": job_salary,
                "salary_increase": increase,
                "salary_increase_pct": increase_pct,
                "match_score": match_score,
                "external_url": job.external_url,
                "remote": job.remote,
            })

        upgrades.sort(key=lambda x: x["salary_increase"], reverse=True)
        return upgrades

    def generate_salary_report(self, user: User) -> Dict:
        """Generate a salary analysis report for upsell"""
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        preferences = self.db.query(UserPreferences).filter(
            UserPreferences.user_id == user.id, UserPreferences.is_active == True
        ).first()

        current_salary = user.current_salary or 0

        all_jobs = self.db.query(Job).filter(
            Job.is_active == True,
            Job.max_salary != None
        ).all()

        salaries = [j.max_salary for j in all_jobs if j.max_salary]
        market_avg = int(sum(salaries) / len(salaries)) if salaries else 0
        market_max = max(salaries) if salaries else 0
        market_min = min(salaries) if salaries else 0

        if preferences and preferences.target_roles:
            role_salaries = []
            for j in all_jobs:
                for role in preferences.target_roles:
                    if role.lower() in (j.title or "").lower():
                        if j.max_salary:
                            role_salaries.append(j.max_salary)
                        break
            role_avg = int(sum(role_salaries) / len(role_salaries)) if role_salaries else market_avg
        else:
            role_avg = market_avg
            role_salaries = salaries

        percentile = 50
        if current_salary > 0 and role_salaries:
            below = len([s for s in role_salaries if s <= current_salary])
            percentile = round((below / len(role_salaries)) * 100)

        upgrades = self.find_salary_upgrades(user, min_increase_pct=5.0)

        return {
            "current_salary": current_salary,
            "market_average": role_avg,
            "market_range": {"min": market_min, "max": market_max},
            "percentile": percentile,
            "potential_increase": role_avg - current_salary if current_salary > 0 else 0,
            "better_paying_jobs": len(upgrades),
            "top_upgrades": upgrades[:5],
            "recommendations": self._generate_recommendations(current_salary, role_avg, percentile),
        }

    def _generate_recommendations(self, current: int, market_avg: int, percentile: int) -> List[str]:
        recs = []
        if current == 0:
            recs.append("Set your current salary to get personalized upgrade alerts")
            return recs

        if percentile < 25:
            recs.append(f"You're in the bottom 25% for your role. Market average is £{market_avg:,}")
            recs.append("Consider negotiating a raise or exploring new opportunities")
        elif percentile < 50:
            recs.append(f"You're below market average (£{market_avg:,}). There's room to grow")
        elif percentile < 75:
            recs.append("You're earning above average - nice work!")
            recs.append("To go higher, focus on leadership roles or specialized skills")
        else:
            recs.append("You're in the top 25% - excellent position!")
            recs.append("Consider management tracks or niche specializations for further growth")

        recs.append("Keep your skills updated - the market rewards continuous learning")
        recs.append("Enable salary upgrade alerts to never miss a higher-paying opportunity")
        return recs
