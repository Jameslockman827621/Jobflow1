from app.tasks import celery_app
from app.services.ai_cv import ai_cv_service
from app.database import SessionLocal
from app.models.application import Application
from app.models.job import Job
from app.models.profile import UserProfile


@celery_app.task
def tailor_cv_for_job(application_id: int):
    """Use AI to tailor CV for a specific job"""
    db = SessionLocal()
    try:
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            return {"error": "Application not found"}
        
        job = db.query(Job).filter(Job.id == application.job_id).first()
        profile = db.query(UserProfile).filter(UserProfile.user_id == application.user_id).first()
        
        if not job or not profile:
            return {"error": "Job or profile not found"}
        
        # Tailor CV
        tailored_cv = ai_cv_service.tailor_cv(
            resume_text=profile.resume_text or "",
            job_description=job.description or "",
            user_profile={
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "current_title": profile.current_title,
                "years_of_experience": profile.years_of_experience,
            }
        )
        
        # Save tailored CV (in production, save to S3)
        application.tailored_cv_url = f"cv_{application_id}.txt"
        db.commit()
        
        return {"status": "completed", "cv_length": len(tailored_cv)}
    finally:
        db.close()


@celery_app.task
def generate_cover_letter_for_job(application_id: int):
    """Generate a targeted cover letter"""
    db = SessionLocal()
    try:
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            return {"error": "Application not found"}
        
        job = db.query(Job).filter(Job.id == application.job_id).first()
        profile = db.query(UserProfile).filter(UserProfile.user_id == application.user_id).first()
        
        if not job or not profile:
            return {"error": "Job or profile not found"}
        
        # Generate cover letter
        cover_letter = ai_cv_service.generate_cover_letter(
            job_description=job.description or "",
            company=job.company,
            user_profile={
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "current_title": profile.current_title,
                "years_of_experience": profile.years_of_experience,
                "skills": [s.name for s in profile.skills],
            }
        )
        
        # Save cover letter
        application.cover_letter = cover_letter
        db.commit()
        
        return {"status": "completed", "cover_letter_length": len(cover_letter)}
    finally:
        db.close()


@celery_app.task
def prepare_application(application_id: int):
    """Full application preparation: CV + cover letter"""
    cv_result = tailor_cv_for_job(application_id)
    cl_result = generate_cover_letter_for_job(application_id)
    
    return {
        "application_id": application_id,
        "cv_result": cv_result,
        "cover_letter_result": cl_result,
    }
