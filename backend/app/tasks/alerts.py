"""
Job Alert Tasks

Scheduled tasks for:
- Daily job alerts (new matching jobs)
- Weekly summary
- Application follow-up reminders
"""

from app.tasks import celery_app
from app.database import SessionLocal
from app.models.user import User
from app.models.profile import UserProfile
from app.models.job import Job
from app.services.matching import JobMatcher
from app.services.email import email_service
from datetime import datetime, timedelta


@celery_app.task
def send_daily_job_alerts():
    """Send daily job alerts to users with new matching jobs"""
    db = SessionLocal()
    try:
        profiles = db.query(UserProfile).all()
        cutoff = datetime.utcnow() - timedelta(hours=24)
        
        alerts_sent = 0
        
        for profile in profiles:
            # Get new jobs in last 24h
            new_jobs = db.query(Job).filter(
                Job.is_active == True,
                Job.created_at > cutoff,
            ).limit(50).all()
            
            if not new_jobs:
                continue
            
            # Find good matches
            matcher = JobMatcher(db)
            matched_jobs = []
            
            for job in new_jobs:
                score = matcher.calculate_match_score(profile, job)
                if score >= 70:  # Only 70%+ matches
                    matched_jobs.append({
                        "title": job.title,
                        "company": job.company,
                        "location": job.location,
                        "url": job.external_url,
                        "score": score,
                    })
            
            # Send alert if we have matches
            if matched_jobs:
                user = db.query(User).filter(User.id == profile.user_id).first()
                if user and user.is_active:
                    email_service.send_job_alert(user.email, matched_jobs[:5])
                    alerts_sent += 1
        
        return {"status": "completed", "alerts_sent": alerts_sent}
    finally:
        db.close()


@celery_app.task
def send_weekly_summary():
    """Send weekly activity summary to users"""
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        cutoff = datetime.utcnow() - timedelta(days=7)
        
        summaries_sent = 0
        
        for user in users:
            # Get user's applications from last week
            from app.models.application import Application
            
            new_apps = db.query(Application).filter(
                Application.user_id == user.id,
                Application.created_at > cutoff,
            ).count()
            
            interviews = db.query(Application).filter(
                Application.user_id == user.id,
                Application.stage.in_(["phone_screen", "technical", "onsite"]),
                Application.created_at > cutoff,
            ).count()
            
            if new_apps > 0 or interviews > 0:
                # Send summary email
                html = f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>Your Weekly Job Search Summary</h2>
                    
                    <div style="display: flex; gap: 20px; margin: 20px 0;">
                        <div style="text-align: center; padding: 20px; background: #eff6ff; border-radius: 8px;">
                            <div style="font-size: 24px; font-weight: bold; color: #2563eb;">{new_apps}</div>
                            <div style="color: #6b7280;">New Applications</div>
                        </div>
                        <div style="text-align: center; padding: 20px; background: #f0fdf4; border-radius: 8px;">
                            <div style="font-size: 24px; font-weight: bold; color: #16a34a;">{interviews}</div>
                            <div style="color: #6b7280;">Interviews</div>
                        </div>
                    </div>
                    
                    <p>Keep up the great work! Consistency is key.</p>
                    
                    <p style="margin-top: 30px;">
                        <a href="http://localhost:3000/dashboard" 
                           style="background-color: #2563eb; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 6px;">
                            View Dashboard
                        </a>
                    </p>
                </body>
                </html>
                """
                email_service.send_email(user.email, "Your Weekly Job Search Summary 📊", html)
                summaries_sent += 1
        
        return {"status": "completed", "summaries_sent": summaries_sent}
    finally:
        db.close()


@celery_app.task
def send_follow_up_reminders():
    """Send reminders to follow up on old applications"""
    db = SessionLocal()
    try:
        from app.models.application import Application
        
        # Applications without response after 7 days
        old_apps = db.query(Application).filter(
            Application.status == "submitted",
            Application.submitted_at < datetime.utcnow() - timedelta(days=7),
        ).all()
        
        reminders_sent = 0
        
        for app in old_apps:
            user = db.query(User).filter(User.id == app.user_id).first()
            if user:
                html = f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>Follow Up Reminder</h2>
                    
                    <p>It's been a week since you applied to:</p>
                    
                    <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 15px 0;">
                        <p style="font-weight: bold; margin: 0;">{app.job.title}</p>
                        <p style="color: #666; margin: 5px 0 0 0;">{app.job.company}</p>
                    </div>
                    
                    <p>Consider sending a follow-up email to the recruiter or hiring manager.</p>
                    
                    <h3>Follow-up Template:</h3>
                    <div style="background: #fef3c7; padding: 15px; border-radius: 6px; font-size: 14px;">
                        <p>Hi [Recruiter Name],</p>
                        <p>I hope this message finds you well. I wanted to follow up on my application for the {app.job.title} position. I'm very interested in this opportunity and would love to discuss how my skills align with your team's needs.</p>
                        <p>Best regards,<br>{user.email}</p>
                    </div>
                </body>
                </html>
                """
                email_service.send_email(user.email, f"Follow up on {app.job.company}", html)
                reminders_sent += 1
        
        return {"status": "completed", "reminders_sent": reminders_sent}
    finally:
        db.close()
