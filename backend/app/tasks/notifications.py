"""
Notification Tasks

Email notifications for:
- Welcome emails
- Application confirmations
- Interview notifications
- Job alerts
"""

from app.tasks import celery_app
from app.database import SessionLocal
from app.models.user import User
from app.models.profile import UserProfile
from app.services.email import email_service


@celery_app.task
def send_welcome_email_task(user_id: int):
    """Send welcome email to new user"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        name = profile.first_name if profile else user.email.split("@")[0]
        
        result = email_service.send_welcome_email(user.email, name)
        return {"status": "sent" if result else "failed", "email": user.email}
    finally:
        db.close()


@celery_app.task
def send_application_confirmation_task(application_id: int):
    """Send application confirmation email"""
    db = SessionLocal()
    try:
        from app.models.application import Application
        from app.models.job import Job
        
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            return {"error": "Application not found"}
        
        job = db.query(Job).filter(Job.id == application.job_id).first()
        if not job:
            return {"error": "Job not found"}
        
        user = db.query(User).filter(User.id == application.user_id).first()
        if not user:
            return {"error": "User not found"}
        
        result = email_service.send_application_confirmation(
            user.email,
            job.title,
            job.company,
        )
        return {"status": "sent" if result else "failed", "email": user.email}
    finally:
        db.close()


@celery_app.task
def send_interview_notification_task(application_id: int, interview_details: str):
    """Send interview notification email"""
    db = SessionLocal()
    try:
        from app.models.application import Application
        from app.models.job import Job
        
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            return {"error": "Application not found"}
        
        job = db.query(Job).filter(Job.id == application.job_id).first()
        if not job:
            return {"error": "Job not found"}
        
        user = db.query(User).filter(User.id == application.user_id).first()
        if not user:
            return {"error": "User not found"}
        
        result = email_service.send_interview_notification(
            user.email,
            job.title,
            job.company,
            interview_details,
        )
        return {"status": "sent" if result else "failed", "email": user.email}
    finally:
        db.close()


@celery_app.task
def send_job_alerts_task():
    """Send daily job alerts to all users"""
    from app.models.job import Job
    from app.services.matching import JobMatcher
    
    db = SessionLocal()
    try:
        profiles = db.query(UserProfile).all()
        
        for profile in profiles:
            # Get recent jobs (last 24h)
            from datetime import datetime, timedelta
            cutoff = datetime.utcnow() - timedelta(days=1)
            
            recent_jobs = db.query(Job).filter(
                Job.is_active == True,
                Job.created_at > cutoff,
            ).limit(10).all()
            
            if recent_jobs:
                # Calculate matches
                matcher = JobMatcher(db)
                matched_jobs = []
                for job in recent_jobs:
                    score = matcher.calculate_match_score(profile, job)
                    if score >= 60:  # Only send 60%+ matches
                        matched_jobs.append({
                            "title": job.title,
                            "company": job.company,
                            "location": job.location,
                            "url": job.external_url,
                            "score": score,
                        })
                
                if matched_jobs:
                    user = db.query(User).filter(User.id == profile.user_id).first()
                    if user:
                        email_service.send_job_alert(user.email, matched_jobs)
        
        return {"status": "completed", "profiles_checked": len(profiles)}
    finally:
        db.close()
