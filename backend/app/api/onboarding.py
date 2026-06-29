"""
Onboarding API

Handles user onboarding flow:
1. Submit preferences
2. Run initial job search
3. Return personalized job feed

Also exposes the viral "quick-start" endpoint: upload CV + pick roles -> done.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.database import get_db
from app.models.user import User
from app.models.preferences import UserPreferences
from app.models.search_cache import SearchCache
from app.services.on_demand_search import OnDemandSearchService
from app.api.auth import get_current_user
from app.core.security import verify_password

router = APIRouter(tags=["Onboarding"])


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
    existing = db.query(UserPreferences).filter_by(
        user_id=current_user.id
    ).first()
    
    if existing:
        for key, value in preferences_data.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        existing.is_active = True
    else:
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
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get suggested companies for user to select.

    Returns companies from our curated directory with ATS metadata so the
    frontend can show which ATS each company uses and the aggregator knows
    where to scrape.

    Query params:
    - query: Search filter (optional)
    - limit: Max results (default 50)
    """
    from app.scrapers.companies import get_company_suggestions
    suggestions = get_company_suggestions(query=query, limit=limit)
    return {"companies": suggestions, "total": len(suggestions)}


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


@router.post("/quick-start")
async def quick_start(
    file: UploadFile = File(...),
    target_roles: str = Form(...),
    seniority_levels: str = Form("mid"),
    locations: str = Form(""),
    remote_preference: str = Form("any"),
    employment_types: str = Form("fulltime"),
    target_companies: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The viral "upload CV + tell us what you want -> done" endpoint.

    Accepts a CV file (PDF/DOCX/TXT) plus role preferences as form fields,
    parses the CV into a structured CV record, saves the user's preferences,
    and immediately runs an on-demand job search. Returns the CV, preferences,
    and the first batch of matched jobs in one response so the frontend can
    drop the user straight onto the dashboard.

    Form fields:
      file:                   CV file (PDF/DOCX/TXT)
      target_roles:           JSON array or comma-separated list, e.g. ["Software Engineer","Backend Developer"]
      seniority_levels:       JSON array or comma-separated list, e.g. ["mid","senior"]
      locations:              JSON array or comma-separated list (optional)
      remote_preference:      "any" | "remote_only" | "hybrid_ok" | "onsite_only"
      employment_types:       JSON array or comma-separated list, e.g. ["fulltime"]
      target_companies:       JSON array or comma-separated list (optional)
    """
    # 1. Upload + parse the CV (reuse the cvs upload logic in-process)
    from app.api.cvs import _extract_text_from_file, _ext_from_content_type, _build_summary_from_parsed
    from app.services.resume_parser import resume_parser
    from app.services.cv_tailor import _extract_keywords
    from app.models.cv import CV
    from app.models.profile import UserProfile
    import os

    filename = (file.filename or "").lower()
    extension = filename.rsplit(".", 1)[-1] if "." in filename else _ext_from_content_type(file.content_type)
    upload_dir = f"uploads/cvs/{current_user.id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/{file.filename or 'cv'}"
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    resume_text = _extract_text_from_file(file_path, extension)
    if not resume_text:
        raise HTTPException(status_code=400, detail="Could not extract any text from the uploaded CV")

    parsed = resume_parser.parse(resume_text)
    contact = parsed.get("contact", {}) or {}
    parsed_skills = [s["name"] for s in (parsed.get("skills") or []) if isinstance(s, dict) and s.get("name")]
    if not parsed_skills:
        parsed_skills = _extract_keywords(resume_text, top_n=15)

    full_name = contact.get("name") or (current_user.email.split("@")[0]).replace(".", " ").title()

    experience = []
    for exp in (parsed.get("experience") or []):
        if isinstance(exp, dict):
            experience.append({
                "company": exp.get("company") or "",
                "role": exp.get("title") or exp.get("role") or "",
                "start_date": exp.get("start_date") or "",
                "end_date": exp.get("end_date") or "",
                "description": exp.get("description") or "",
            })

    # Clear primary flag on other CVs
    db.query(CV).filter(CV.user_id == current_user.id, CV.is_primary == True).update({CV.is_primary: False})
    cv = CV(
        user_id=current_user.id,
        full_name=full_name,
        email=contact.get("email") or current_user.email,
        phone=contact.get("phone") or "",
        location=contact.get("location") or "",
        linkedin_url=contact.get("linkedin") or "",
        portfolio_url=contact.get("github") or "",
        summary=_build_summary_from_parsed(parsed, parsed_skills),
        experience=experience,
        education=parsed.get("education") or [],
        skills=parsed_skills,
        certifications=parsed.get("certifications") or [],
        template_id="modern",
        file_path=file_path,
        is_ai_generated=False,
        is_primary=True,
    )
    db.add(cv)

    # Sync profile
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if profile:
            profile.resume_text = resume_text[:8000]
            if contact.get("location"):
                profile.location = contact["location"]
        else:
            profile = UserProfile(
                user_id=current_user.id,
                first_name=full_name.split(" ")[0] if full_name else "",
                last_name=" ".join(full_name.split(" ")[1:]) if full_name and " " in full_name else "",
                location=contact.get("location") or "",
                resume_text=resume_text[:8000],
            )
            db.add(profile)
    except Exception as e:
        print(f"  quick_start: profile sync error: {e}")

    # 2. Parse preference form fields (accept JSON or comma-separated)
    def _parse_list(raw):
        if not raw:
            return []
        raw = raw.strip()
        if raw.startswith("["):
            try:
                return json.loads(raw)
            except Exception:
                pass
        return [x.strip() for x in raw.split(",") if x.strip()]

    prefs_data = {
        "target_roles": _parse_list(target_roles),
        "seniority_levels": _parse_list(seniority_levels),
        "locations": _parse_list(locations),
        "remote_preference": remote_preference or "any",
        "employment_types": _parse_list(employment_types),
        "target_companies": _parse_list(target_companies),
        "date_posted": "month",
    }

    # 3. Save preferences (upsert)
    existing_pref = db.query(UserPreferences).filter_by(user_id=current_user.id).first()
    if existing_pref:
        for k, v in prefs_data.items():
            if hasattr(existing_pref, k):
                setattr(existing_pref, k, v)
        existing_pref.is_active = True
        preferences = existing_pref
    else:
        preferences = UserPreferences.from_dict(prefs_data, current_user.id)
        db.add(preferences)

    db.commit()
    db.refresh(cv)
    db.refresh(preferences)

    # 4. Run on-demand search immediately
    search_service = OnDemandSearchService(db)
    search_result = await search_service.search_for_user(
        user_id=current_user.id,
        preferences=preferences,
        force_refresh=True,
    )

    return {
        "status": "ready",
        "cv": {
            "id": cv.id,
            "full_name": cv.full_name,
            "skills": cv.skills,
            "experience_count": len(cv.experience or []),
        },
        "preferences": preferences.to_dict(),
        "jobs": search_result.get("jobs", []),
        "total_jobs": search_result.get("total", 0),
        "sources_used": search_result.get("sources_used", {}),
        "message": f"CV parsed and {search_result.get('total', 0)} matching jobs found.",
    }


@router.get("/me")
async def get_my_onboarding(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current user's onboarding state — CV, preferences, and stats."""
    from app.models.cv import CV
    preferences = db.query(UserPreferences).filter_by(user_id=current_user.id).first()
    primary_cv = db.query(CV).filter(CV.user_id == current_user.id, CV.is_primary == True).first()
    if not primary_cv:
        primary_cv = db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.created_at.desc()).first()
    return {
        "has_preferences": preferences is not None,
        "has_cv": primary_cv is not None,
        "preferences": preferences.to_dict() if preferences else None,
        "cv": {
            "id": primary_cv.id,
            "full_name": primary_cv.full_name,
            "skills": primary_cv.skills or [],
            "experience_count": len(primary_cv.experience or []),
        } if primary_cv else None,
    }
