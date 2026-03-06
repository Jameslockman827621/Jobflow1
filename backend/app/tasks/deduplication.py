"""
Celery tasks for job deduplication

Scheduled to run daily to clean up duplicate jobs.
"""

from app.tasks import celery_app
from app.database import SessionLocal
from app.services.deduplication import JobDeduplicator
from datetime import datetime


@celery_app.task
def remove_duplicate_jobs():
    """
    Remove duplicate jobs from the database.
    
    Runs daily at 2 AM via Celery Beat.
    """
    db = SessionLocal()
    
    try:
        deduplicator = JobDeduplicator(db)
        
        # Get stats before cleanup
        stats_before = deduplicator.get_duplicate_stats()
        
        # Remove duplicates in batches
        result = deduplicator.remove_duplicates(batch_size=500)
        
        # Get stats after cleanup
        stats_after = deduplicator.get_duplicate_stats()
        
        return {
            "status": "completed",
            "removed": result["removed"],
            "batches": result["batches"],
            "stats_before": stats_before,
            "stats_after": stats_after,
            "improvement": stats_before.get("duplicate_percentage", 0) - stats_after.get("duplicate_percentage", 0)
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }
    finally:
        db.close()


@celery_app.task
def check_duplicate_before_insert(job_data: dict):
    """
    Check if a job would be a duplicate before inserting.
    
    Can be called from scraper tasks before saving jobs.
    
    Args:
        job_data: Dict with job attributes (company, title, location, external_url, etc.)
    
    Returns:
        Dict with is_duplicate flag and reason
    """
    db = SessionLocal()
    
    try:
        deduplicator = JobDeduplicator(db)
        is_duplicate, reason = deduplicator.prevent_duplicate_on_insert(job_data)
        
        return {
            "is_duplicate": is_duplicate,
            "reason": reason,
            "should_insert": not is_duplicate
        }
        
    except Exception as e:
        return {
            "is_duplicate": False,  # Fail open - allow insert on error
            "reason": f"Error checking: {e}",
            "should_insert": True
        }
    finally:
        db.close()


@celery_app.task
def get_duplicate_stats():
    """
    Get current duplicate statistics.
    
    Useful for monitoring and alerting.
    """
    db = SessionLocal()
    
    try:
        deduplicator = JobDeduplicator(db)
        stats = deduplicator.get_duplicate_stats()
        
        return {
            "status": "completed",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }
    finally:
        db.close()
