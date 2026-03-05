from app.tasks import celery_app


@celery_app.task
def tailor_cv_for_job(application_id: int, job_description: str):
    """
    Use AI to tailor CV for a specific job.
    TODO: Implement with LLM integration.
    """
    print(f"Tailoring CV for application {application_id}")
    # TODO: Call LLM to rewrite CV based on job description
    return {"status": "completed"}


@celery_app.task
def generate_cover_letter(application_id: int, job_description: str, user_profile: dict):
    """
    Generate a targeted cover letter.
    TODO: Implement with LLM integration.
    """
    print(f"Generating cover letter for application {application_id}")
    # TODO: Call LLM to generate cover letter
    return {"status": "completed", "cover_letter": "TODO"}
