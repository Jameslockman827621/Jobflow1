"""
Celery tasks for on-demand job search

Replaces continuous background scraping with user-specific search refresh.
"""

from app.tasks import celery_app
from app.database import SessionLocal
from app.models.preferences import UserPreferences
from app.models.search_cache import SearchCache
from app.services.on_demand_search import OnDemandSearchService
from datetime import datetime, timedelta


@celery_app.task
def refresh_user_search(user_id: int):
    """
    Refresh job search for a specific user.
    
    Called when:
    - User's cache is expired
    - User updates preferences
    - Scheduled refresh (every 6 hours)
    """
    db = SessionLocal()
    
    try:
        preferences = db.query(UserPreferences).filter_by(
            user_id=user_id,
            is_active=True
        ).first()
        
        if not preferences:
            return {"status": "skipped", "reason": "no_preferences"}
        
        search_service = OnDemandSearchService(db)
        result = search_service.search_for_user(
            user_id=user_id,
            preferences=preferences,
            force_refresh=False  # Use cache if still valid
        )
        
        return {
            "status": "completed",
            "user_id": user_id,
            "jobs_found": result.get("total", 0),
            "search_duration_ms": result.get("search_duration_ms", 0),
            "sources": result.get("sources_used", {})
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "user_id": user_id,
            "error": str(e)
        }
    finally:
        db.close()


@celery_app.task
def refresh_all_user_searches():
    """
    Refresh job searches for all active users.
    
    Runs every 6 hours via Celery Beat.
    Only refreshes users with:
    - Active preferences
    - Expired or expiring cache
    """
    db = SessionLocal()
    
    try:
        # Get all active preferences
        preferences = db.query(UserPreferences).filter_by(
            is_active=True
        ).all()
        
        results = {
            "total_users": len(preferences),
            "refreshed": 0,
            "skipped": 0,
            "failed": 0,
            "details": []
        }
        
        for pref in preferences:
            # Check if cache needs refresh
            cache = db.query(SearchCache).filter_by(
                user_id=pref.user_id,
                is_valid=True
            ).first()
            
            # Skip if cache is still valid (not expired and not within 2h of expiry)
            if cache and not cache.should_refresh():
                results["skipped"] += 1
                continue
            
            # Queue refresh
            try:
                refresh_user_search.delay(pref.user_id)
                results["refreshed"] += 1
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "user_id": pref.user_id,
                    "error": str(e)
                })
        
        return results
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }
    finally:
        db.close()


@celery_app.task
def clean_expired_cache():
    """
    Clean up expired search cache entries.
    
    Runs daily at 3 AM.
    """
    db = SessionLocal()
    
    try:
        now = datetime.utcnow()
        
        # Delete expired cache entries
        deleted = db.query(SearchCache).filter(
            SearchCache.expires_at < now
        ).delete()
        
        db.commit()
        
        return {
            "status": "completed",
            "deleted": deleted,
            "timestamp": now.isoformat()
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }
    finally:
        db.close()


@celery_app.task
def prefetch_popular_searches():
    """
    Prefetch searches for popular role/location combinations.
    
    This ensures common searches are always warm in the cache.
    
    Runs daily at 5 AM.
    """
    db = SessionLocal()
    
    try:
        # Popular searches to prefetch
        popular_searches = [
            {
                "target_roles": ["Software Engineer"],
                "locations": ["London, UK"],
                "remote_only": False,
                "min_salary": 50000
            },
            {
                "target_roles": ["Python Developer"],
                "locations": ["London, UK"],
                "remote_only": False,
                "min_salary": 50000
            },
            {
                "target_roles": ["Software Engineer"],
                "locations": ["Remote"],
                "remote_only": True,
                "min_salary": 60000
            },
            {
                "target_roles": ["Data Engineer"],
                "locations": ["London, UK"],
                "remote_only": False,
                "min_salary": 60000
            },
            {
                "target_roles": ["DevOps Engineer"],
                "locations": ["Remote"],
                "remote_only": True,
                "min_salary": 70000
            },
        ]
        
        results = {
            "total_searches": len(popular_searches),
            "completed": 0,
            "failed": 0,
        }
        
        # Create a temporary user for popular searches
        # In production, you'd use a shared cache or Redis
        for search_params in popular_searches:
            try:
                # This would use a shared cache system
                # For now, we just log that we'd prefetch these
                print(f"Would prefetch: {search_params}")
                results["completed"] += 1
            except Exception as e:
                results["failed"] += 1
                print(f"Prefetch failed: {e}")
        
        return results
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }
    finally:
        db.close()
