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
    """Upload existing CV (PDF/DOCX)"""
    # Validate file type
    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")
    
    # Save file
    upload_dir = f"uploads/cvs/{current_user.id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = f"{upload_dir}/{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create CV record
    cv = CV(
        user_id=current_user.id,
        full_name=current_user.email.split("@")[0],  # Placeholder
        email=current_user.email,
        file_path=file_path,
        is_ai_generated=False
    )
    
    db.add(cv)
    db.commit()
    db.refresh(cv)
    
    return {
        "cv_id": cv.id,
        "file_path": file_path,
        "message": "CV uploaded successfully. You can now edit the parsed content."
    }


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


@router.get("/{cv_id}/pdf")
async def export_cv_pdf(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export a real PDF resume for ATS file uploads (extension + headless)."""
    from app.models.profile import UserProfile
    from app.services.apply_engine import build_applicant_payload
    from app.services.resume_files import build_minimal_pdf, ensure_resume_local_path, is_real_pdf

    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    # Prefer an uploaded real PDF on disk
    if cv.file_path and os.path.isfile(cv.file_path) and is_real_pdf(cv.file_path):
        with open(cv.file_path, "rb") as f:
            data = f.read()
        filename = os.path.basename(cv.file_path) or f"cv_{cv_id}.pdf"
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    payload = build_applicant_payload(current_user, profile, cv)
    path = ensure_resume_local_path(current_user.id, payload, cv)
    if path and os.path.isfile(path) and is_real_pdf(path):
        with open(path, "rb") as f:
            data = f.read()
    else:
        from app.services.resume_files import _format_resume_text

        data = build_minimal_pdf(_format_resume_text(payload, cv))

    safe_name = (cv.full_name or f"cv_{cv_id}").replace(" ", "_")
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.pdf"'},
    )


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
