"""
Onboarding API

Handles user onboarding flow:
1. Submit preferences
2. Run initial job search
3. Return personalized job feed
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.preferences import UserPreferences
from app.models.search_cache import SearchCache
from app.services.on_demand_search import OnDemandSearchService
from app.api.auth import get_current_user
from app.core.security import verify_password

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.post("/preferences")
async def submit_preferences(
    preferences_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit job preferences during onboarding.
    
    This triggers an immediate job search and returns personalized results.
    
    Request body:
    {
        "target_roles": ["Software Engineer", "Senior Developer"],
        "locations": ["London, UK", "Remote"],
        "remote_only": false,
        "hybrid_ok": true,
        "min_salary": 60000,
        "target_companies": ["Stripe", "Figma", "Airbnb"],
        "seniority_levels": ["mid", "senior"],
        "required_skills": ["Python", "AWS"],
        "employment_types": ["FULL_TIME"]
    }
    """
    # Check if preferences already exist
    existing = db.query(UserPreferences).filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if existing:
        # Update existing preferences
        for key, value in preferences_data.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
    else:
        # Create new preferences
        existing = UserPreferences.from_dict(preferences_data, current_user.id)
        db.add(existing)
    
    db.commit()
    db.refresh(existing)
    
    return {
        "status": "success",
        "message": "Preferences saved",
        "preferences": existing.to_dict()
    }


@router.post("/search")
async def run_job_search(
    force_refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run on-demand job search based on user preferences.
    
    Returns fresh jobs from LinkedIn, Greenhouse, and Lever.
    Results are cached for 24 hours.
    
    Query params:
    - force_refresh: Skip cache and run fresh search
    """
    # Get user preferences
    preferences = db.query(UserPreferences).filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if not preferences:
        raise HTTPException(
            status_code=400,
            detail="User preferences not found. Please complete onboarding first."
        )
    
    # Run search
    search_service = OnDemandSearchService(db)
    result = await search_service.search_for_user(
        user_id=current_user.id,
        preferences=preferences,
        force_refresh=force_refresh
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return {
        "status": result["status"],
        "message": result["message"],
        "jobs": result["jobs"],
        "total": result["total"],
        "cache": result.get("cache"),
        "search_duration_ms": result.get("search_duration_ms"),
        "sources_used": result.get("sources_used")
    }


@router.get("/jobs")
async def get_cached_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user's cached job search results (for extension popup).
    Returns jobs from the most recent search. Does not run a new search.
    """
    cache = (
        db.query(SearchCache)
        .filter_by(user_id=current_user.id)
        .order_by(SearchCache.created_at.desc())
        .first()
    )
    if not cache or not cache.job_ids:
        return {"jobs": [], "total": 0}

    search_service = OnDemandSearchService(db)
    jobs = search_service._fetch_jobs_by_ids(cache.job_ids)
    return {"jobs": jobs, "total": len(jobs)}


@router.get("/status")
async def get_onboarding_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check onboarding status for current user.
    
    Returns:
    - Has preferences?
    - Has cached jobs?
    - When was last search?
    """
    preferences = db.query(UserPreferences).filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()
    
    cache = None
    if preferences:
        cache = db.query(SearchCache).filter_by(
            user_id=current_user.id,
            is_valid=True
        ).order_by(SearchCache.created_at.desc()).first()
    
    return {
        "onboarding_complete": preferences is not None,
        "has_preferences": preferences is not None,
        "has_cached_jobs": cache is not None and cache.job_ids and len(cache.job_ids) > 0,
        "preferences": preferences.to_dict() if preferences else None,
        "cache": cache.to_dict() if cache else None,
        "cache_expired": cache.is_expired() if cache else None,
        "next_refresh": cache.expires_at.isoformat() if cache else None
    }


@router.put("/preferences")
async def update_preferences(
    preferences_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update existing preferences.
    
    Partial updates allowed - only provided fields will be updated.
    """
    preferences = db.query(UserPreferences).filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if not preferences:
        raise HTTPException(
            status_code=404,
            detail="Preferences not found. Please complete onboarding first."
        )
    
    # Update only provided fields
    for key, value in preferences_data.items():
        if hasattr(preferences, key):
            setattr(preferences, key, value)
    
    db.commit()
    db.refresh(preferences)
    
    return {
        "status": "success",
        "message": "Preferences updated",
        "preferences": preferences.to_dict()
    }


@router.delete("/preferences")
async def delete_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete user preferences (reset onboarding).
    
    Also clears cached search results.
    """
    preferences = db.query(UserPreferences).filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if not preferences:
        raise HTTPException(status_code=404, detail="Preferences not found")
    
    # Mark as inactive (soft delete)
    preferences.is_active = False
    
    # Clear cache
    db.query(SearchCache).filter_by(
        user_id=current_user.id
    ).delete()
    
    db.commit()
    
    return {
        "status": "success",
        "message": "Preferences deleted. You can restart onboarding anytime."
    }


@router.get("/companies/suggested")
async def get_suggested_companies(
    query: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get suggested companies for user to select.
    
    Query params:
    - query: Search filter (optional)
    - limit: Max results (default 20)
    """
    # Curated list of top tech companies
    suggested = [
        {"name": "Stripe", "industry": "Fintech", "size": "mid"},
        {"name": "Figma", "industry": "Design", "size": "mid"},
        {"name": "Airbnb", "industry": "Travel", "size": "enterprise"},
        {"name": "GitLab", "industry": "DevTools", "size": "mid"},
        {"name": "Monzo", "industry": "Fintech", "size": "mid"},
        {"name": "Revolut", "industry": "Fintech", "size": "enterprise"},
        {"name": "Coinbase", "industry": "Crypto", "size": "enterprise"},
        {"name": "Shopify", "industry": "E-commerce", "size": "enterprise"},
        {"name": "Zendesk", "industry": "SaaS", "size": "enterprise"},
        {"name": "Twitch", "industry": "Entertainment", "size": "enterprise"},
        {"name": "Dropbox", "industry": "Cloud", "size": "enterprise"},
        {"name": "Snowflake", "industry": "Data", "size": "enterprise"},
        {"name": "Databricks", "industry": "Data/AI", "size": "mid"},
        {"name": "Anthropic", "industry": "AI", "size": "startup"},
        {"name": "OpenAI", "industry": "AI", "size": "mid"},
        {"name": "Notion", "industry": "Productivity", "size": "mid"},
        {"name": "Linear", "industry": "Productivity", "size": "startup"},
        {"name": "Vercel", "industry": "DevTools", "size": "startup"},
        {"name": "Supabase", "industry": "DevTools", "size": "startup"},
        {"name": "Plaid", "industry": "Fintech", "size": "mid"},
    ]
    
    # Filter by query if provided
    if query:
        query_lower = query.lower()
        suggested = [
            c for c in suggested
            if query_lower in c["name"].lower() or query_lower in c["industry"].lower()
        ]
    
    return {
        "companies": suggested[:limit],
        "total": len(suggested)
    }


@router.get("/roles/suggested")
async def get_suggested_roles(
    query: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get suggested job roles.
    
    Query params:
    - query: Search filter (optional)
    - limit: Max results (default 20)
    """
    suggested = [
        "Software Engineer",
        "Senior Software Engineer",
        "Staff Software Engineer",
        "Principal Engineer",
        "Frontend Developer",
        "Backend Developer",
        "Full Stack Developer",
        "Python Developer",
        "Java Developer",
        "JavaScript Developer",
        "React Developer",
        "Node.js Developer",
        "DevOps Engineer",
        "Site Reliability Engineer",
        "Data Engineer",
        "Data Scientist",
        "Machine Learning Engineer",
        "AI Engineer",
        "Product Manager",
        "Product Designer",
    ]
    
    # Filter by query if provided
    if query:
        query_lower = query.lower()
        suggested = [r for r in suggested if query_lower in r.lower()]
    
    return {
        "roles": suggested[:limit],
        "total": len(suggested)
    }
