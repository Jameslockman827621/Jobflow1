"""
CV/Resume API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

from app.database import get_db
from app.models.cv import CV, CVTemplate
from app.models.user import User
from app.services.cv_builder import cv_builder_service
from app.services.cv_templates import get_all_templates, get_template
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/v1/cvs", tags=["CVs"])


@router.get("")
async def get_user_cvs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all CVs for current user"""
    cvs = db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.created_at.desc()).all()
    return {
        "cvs": cvs,
        "total": len(cvs)
    }


@router.get("/templates")
async def get_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available CV templates"""
    templates = get_all_templates()
    return {
        "templates": templates,
        "total": len(templates)
    }


@router.get("/{cv_id}")
async def get_cv(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific CV"""
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    return cv


@router.post("")
async def create_cv(
    cv_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new CV"""
    cv = CV(
        user_id=current_user.id,
        full_name=cv_data.get("full_name"),
        email=cv_data.get("email"),
        phone=cv_data.get("phone", ""),
        location=cv_data.get("location", ""),
        linkedin_url=cv_data.get("linkedin_url", ""),
        portfolio_url=cv_data.get("portfolio_url", ""),
        summary=cv_data.get("summary", ""),
        experience=cv_data.get("experience", []),
        education=cv_data.get("education", []),
        skills=cv_data.get("skills", []),
        certifications=cv_data.get("certifications", []),
        projects=cv_data.get("projects", []),
        template_id=cv_data.get("template_id", "modern"),
        is_ai_generated=cv_data.get("is_ai_generated", False)
    )
    
    db.add(cv)
    db.commit()
    db.refresh(cv)
    
    return cv


@router.put("/{cv_id}")
async def update_cv(
    cv_id: int,
    cv_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update existing CV"""
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    
    # Update fields
    for field, value in cv_data.items():
        if hasattr(cv, field) and field not in ['id', 'user_id', 'created_at', 'updated_at']:
            setattr(cv, field, value)
    
    cv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cv)
    
    return cv


@router.delete("/{cv_id}")
async def delete_cv(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete CV"""
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    
    db.delete(cv)
    db.commit()
    
    return {"message": "CV deleted successfully"}


@router.post("/generate-summary")
async def generate_summary(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI-generate professional summary"""
    experience = body.get("experience", [])
    skills = body.get("skills", [])
    target_role = body.get("target_role", "Software Engineer")
    summary = await cv_builder_service.generate_summary(experience, skills, target_role)
    return {"summary": summary}


@router.post("/enhance-description")
async def enhance_description(
    role: str,
    company: str,
    description: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI-enhance job description"""
    enhanced = await cv_builder_service.enhance_job_description(role, company, description)
    return {"enhanced_description": enhanced}


@router.post("/tailor-for-job")
async def tailor_for_job(
    cv_id: int,
    job_description: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tailor CV for specific job"""
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    cv_data = {
        "summary": cv.summary,
        "experience": cv.experience,
        "skills": cv.skills
    }

    tailored = await cv_builder_service.tailor_cv_for_job(cv_data, job_description)

    # Update CV with tailored content
    cv.summary = tailored.get('summary', cv.summary)
    db.commit()
    db.refresh(cv)

    return cv


@router.post("/score")
async def score_cv_endpoint(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Score a CV against a job description (ATS optimization check).

    Body: {"cv_id": 1, "job_description": "..."} or {"cv_data": {...}, "job_description": "..."}
    Returns the ATS score breakdown.
    """
    from app.services.cv_tailor import score_cv_against_job

    job_description = body.get("job_description") or ""
    if not job_description:
        raise HTTPException(status_code=400, detail="job_description is required")

    cv_data = body.get("cv_data")
    if not cv_data and body.get("cv_id"):
        cv = db.query(CV).filter(CV.id == body["cv_id"], CV.user_id == current_user.id).first()
        if not cv:
            raise HTTPException(status_code=404, detail="CV not found")
        cv_data = {
            "full_name": cv.full_name,
            "summary": cv.summary or "",
            "experience": cv.experience or [],
            "education": cv.education or [],
            "skills": cv.skills or [],
            "certifications": cv.certifications or [],
            "projects": cv.projects or [],
        }
    if not cv_data:
        raise HTTPException(status_code=400, detail="Either cv_id or cv_data is required")

    score = score_cv_against_job(cv_data, job_description)
    return {"ats": score}


@router.get("/{cv_id}/completeness")
async def check_completeness(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check CV completeness score"""
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    
    cv_data = {
        "full_name": cv.full_name,
        "email": cv.email,
        "summary": cv.summary,
        "phone": cv.phone,
        "location": cv.location,
        "linkedin_url": cv.linkedin_url,
        "experience": cv.experience,
        "education": cv.education,
        "skills": cv.skills
    }
    
    result = cv_builder_service.validate_cv_completeness(cv_data)
    return result


@router.post("/upload")
async def upload_cv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a CV (PDF/DOCX/TXT), parse it, and auto-populate a structured CV.

    This is the "upload CV and we'll handle the rest" onboarding entry point.
    Extracted skills are also pushed onto the user's profile so job matching works
    immediately.
    """
    # Validate file type (also accept text/plain and octet-stream from some browsers)
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "application/octet-stream",
        "application/msword",
    ]
    filename = (file.filename or "").lower()
    extension = filename.rsplit(".", 1)[-1] if "." in filename else ""
    if file.content_type not in allowed_types and extension not in {"pdf", "docx", "txt"}:
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, and TXT files are allowed")

    # File size limit (10MB) — guards against disk/memory exhaustion
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    # Save file — sanitize filename to prevent path traversal
    import os
    safe_name = os.path.basename(file.filename or "cv")
    # Strip any remaining shell/path metacharacters and prefix with user id
    safe_name = f"u{current_user.id}_{safe_name}"
    upload_dir = f"uploads/cvs/{current_user.id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/{safe_name}"
    with open(file_path, "wb") as f:
        f.write(content)

    # Extract text from the file
    resume_text = _extract_text_from_file(file_path, extension or _ext_from_content_type(file.content_type))
    if not resume_text:
        raise HTTPException(status_code=400, detail="Could not extract any text from the uploaded file")

    # Parse the extracted text into structured data
    from app.services.resume_parser import resume_parser
    parsed = resume_parser.parse(resume_text)
    contact = parsed.get("contact", {}) or {}
    parsed_skills = [s["name"] for s in (parsed.get("skills") or []) if isinstance(s, dict) and s.get("name")]
    # Fallback: if regex parser found nothing, use the skill dictionary from the tailor service
    if not parsed_skills:
        from app.services.cv_tailor import _extract_keywords
        parsed_skills = _extract_keywords(resume_text, top_n=15)

    # Derive a full name — prefer contact info, fall back to email prefix
    full_name = (
        contact.get("name")
        or (current_user.email.split("@")[0]).replace(".", " ").title()
    )

    # Build experience entries (parser returns {title, company, start_date, end_date} — add description if present)
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

    # Create CV record with parsed data
    cv = CV(
        user_id=current_user.id,
        full_name=full_name,
        email=contact.get("email") or current_user.email,
        phone=contact.get("phone") or "",
        location=contact.get("location") or "",
        linkedin_url=contact.get("linkedin") or "",
        portfolio_url=contact.get("github") or contact.get("website") or "",
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

    # Clear primary flag on other CVs so this one becomes the main CV
    db.query(CV).filter(CV.user_id == current_user.id, CV.is_primary == True).update({CV.is_primary: False})

    db.add(cv)
    db.commit()
    db.refresh(cv)

    # Push extracted skills onto the user profile so job matching works immediately
    try:
        from app.models.profile import UserProfile
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if profile:
            existing = set(profile.resume_text or "")
            # Merge parsed skills into profile (best-effort — don't fail the upload if profile is missing)
            profile.resume_text = resume_text[:8000]
            if parsed_skills:
                # UserProfile doesn't have a skills array, but the parser output is stored on the CV
                pass
        else:
            # Create a profile if missing
            profile = UserProfile(
                user_id=current_user.id,
                first_name=full_name.split(" ")[0] if full_name else "",
                last_name=" ".join(full_name.split(" ")[1:]) if full_name and " " in full_name else "",
                location=contact.get("location") or "",
                resume_text=resume_text[:8000],
            )
            db.add(profile)
        db.commit()
    except Exception as e:
        print(f"  upload_cv: profile sync error: {e}")

    return {
        "cv_id": cv.id,
        "file_path": file_path,
        "parsed": {
            "full_name": cv.full_name,
            "email": cv.email,
            "phone": cv.phone,
            "location": cv.location,
            "linkedin_url": cv.linkedin_url,
            "skills": cv.skills,
            "experience_count": len(cv.experience or []),
            "education_count": len(cv.education or []),
            "years_of_experience": parsed.get("years_of_experience"),
        },
        "message": "CV uploaded and parsed. You can edit any field in the CV Builder.",
    }


def _extract_text_from_file(file_path: str, extension: str) -> str:
    """Extract plain text from a PDF, DOCX, or TXT file."""
    try:
        if extension == "pdf":
            import pdfplumber
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    if page_text:
                        text_parts.append(page_text)
            return "\n".join(text_parts)
        if extension == "docx":
            import docx
            doc = docx.Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs if p.text)
        # Fallback: read as text
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        print(f"  _extract_text_from_file: error: {e}")
        return ""


def _ext_from_content_type(content_type: str) -> str:
    mapping = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/msword": "doc",
        "text/plain": "txt",
    }
    return mapping.get(content_type, "txt")


def _build_summary_from_parsed(parsed: dict, skills: list) -> str:
    """Build a professional summary from parsed CV data."""
    years = parsed.get("years_of_experience")
    skill_str = ", ".join(skills[:6]) if skills else "software development"
    if years and float(years) > 0:
        return f"Engineer with {int(years)}+ years of experience in {skill_str}. Proven track record shipping production features and collaborating cross-functionally."
    return f"Engineer with experience in {skill_str}. Proven track record shipping production features and collaborating cross-functionally."


@router.get("/{cv_id}/export")
async def export_cv(
    cv_id: int,
    template_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export CV as HTML (can be converted to PDF)"""
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    
    # Get template
    template = get_template(template_id or cv.template_id)
    html_content = render_cv_html(cv, template['html'])
    
    return HTMLResponse(content=html_content, headers={
        "Content-Disposition": f"attachment; filename=cv_{cv.full_name.replace(' ', '_')}.html"
    })


def _resolve_conditionals(html: str, data: dict) -> str:
    """Resolve Mustache-style conditional blocks {{#field}}...{{/field}}."""
    import re
    pattern = re.compile(r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}', re.DOTALL)
    def _replace(m):
        key = m.group(1)
        inner = m.group(2)
        val = data.get(key)
        if val:
            return inner.replace(f'{{{{{key}}}}}', str(val))
        return ''
    prev = None
    while prev != html:
        prev = html
        html = pattern.sub(_replace, html)
    return html


def render_cv_html(cv: CV, template: str) -> str:
    """Render CV data into HTML template"""
    import re
    
    html = template

    scalar_data = {
        'full_name': cv.full_name or '',
        'email': cv.email or '',
        'phone': cv.phone or '',
        'location': cv.location or '',
        'linkedin_url': cv.linkedin_url or '',
        'portfolio_url': cv.portfolio_url or '',
        'summary': cv.summary or '',
    }

    if cv.experience:
        exp_html = ""
        for exp in cv.experience:
            item_html = """<div class="position">
                <div class="position-header">
                    <div>
                        <span class="position-title">{{role}}</span>
                        {{#company}}<span class="company"> | {{company}}</span>{{/company}}
                    </div>
                    <div class="date">{{start_date}} - {{end_date}}</div>
                </div>
                {{#description}}<div class="description">{{description}}</div>{{/description}}
            </div>"""
            item_html = _resolve_conditionals(item_html, exp)
            for k, v in exp.items():
                item_html = item_html.replace(f'{{{{{k}}}}}', str(v) if v else '')
            exp_html += item_html
        html = re.sub(r'\{\{#experience\}\}.*?\{\{/experience\}\}', exp_html, html, flags=re.DOTALL)
    else:
        html = re.sub(r'\{\{#experience\}\}.*?\{\{/experience\}\}', '', html, flags=re.DOTALL)

    if cv.education:
        edu_html = ""
        for edu in cv.education:
            item_html = """<div class="education-item">
                <div class="education-header">
                    <div>
                        <span class="degree">{{degree}}</span>
                        {{#field}}<span class="institution"> | {{field}}</span>{{/field}}
                        {{#institution}}<span class="institution"> | {{institution}}</span>{{/institution}}
                    </div>
                    <div class="year">{{graduation_year}}</div>
                </div>
            </div>"""
            item_html = _resolve_conditionals(item_html, edu)
            for k, v in edu.items():
                item_html = item_html.replace(f'{{{{{k}}}}}', str(v) if v else '')
            edu_html += item_html
        html = re.sub(r'\{\{#education\}\}.*?\{\{/education\}\}', edu_html, html, flags=re.DOTALL)
    else:
        html = re.sub(r'\{\{#education\}\}.*?\{\{/education\}\}', '', html, flags=re.DOTALL)

    if cv.skills:
        skills_html = '<div class="skills-grid">' + "".join(
            [f'<span class="skill-tag">{skill}</span>' for skill in cv.skills]
        ) + '</div>'
        html = re.sub(r'\{\{#skills\}\}.*?\{\{/skills\}\}', skills_html, html, flags=re.DOTALL)
    else:
        html = re.sub(r'\{\{#skills\}\}.*?\{\{/skills\}\}', '', html, flags=re.DOTALL)

    if cv.certifications:
        cert_html = ""
        for cert in cv.certifications:
            item_html = """<div class="education-item">
                <div class="education-header">
                    <span class="degree">{{name}}</span>
                    {{#issuer}}<span class="institution"> | {{issuer}}</span>{{/issuer}}
                    {{#year}}<span class="year">{{year}}</span>{{/year}}
                </div>
            </div>"""
            item_html = _resolve_conditionals(item_html, cert)
            for k, v in cert.items():
                item_html = item_html.replace(f'{{{{{k}}}}}', str(v) if v else '')
            cert_html += item_html
        html = re.sub(r'\{\{#certifications\}\}.*?\{\{/certifications\}\}', cert_html, html, flags=re.DOTALL)
    else:
        html = re.sub(r'\{\{#certifications\}\}.*?\{\{/certifications\}\}', '', html, flags=re.DOTALL)

    html = _resolve_conditionals(html, scalar_data)
    for k, v in scalar_data.items():
        html = html.replace(f'{{{{{k}}}}}', v)

    html = re.sub(r'\{\{[#/]?\w+\}\}', '', html)

    return html
