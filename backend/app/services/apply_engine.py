"""
Apply engine: build fill packages for extension + headless workers.

Supports text, select, radio, checkbox, file, textarea, and open-ended
questions answered in the user's voice (from profile/CV + optional LLM).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.application import Application
from app.models.cv import CV
from app.models.job import Job
from app.models.profile import UserProfile
from app.models.user import User

logger = logging.getLogger(__name__)


ATS_PATTERNS = {
    "greenhouse": [r"greenhouse\.io", r"boards\.greenhouse", r"job-boards\.greenhouse"],
    "lever": [r"lever\.co", r"jobs\.lever"],
    "workable": [r"workable\.com", r"apply\.workable"],
    "ashby": [r"ashbyhq\.com", r"jobs\.ashbyhq"],
    "workday": [r"myworkdayjobs\.com", r"workday\.com"],
    "linkedin": [r"linkedin\.com/jobs"],
    "indeed": [r"indeed\.com"],
}


FIELD_ALIASES = {
    "first_name": ["first name", "firstname", "first_name", "given name", "fname"],
    "last_name": ["last name", "lastname", "last_name", "surname", "family name", "lname"],
    "full_name": ["full name", "name", "your name", "applicant name"],
    "email": ["email", "e-mail", "email address", "work email"],
    "phone": ["phone", "telephone", "mobile", "phone number", "cell", "tel"],
    "linkedin": ["linkedin", "linkedin url", "linkedin profile", "linkedin.com"],
    "portfolio": ["portfolio", "website", "personal website", "github", "portfolio url"],
    "location": ["location", "city", "current location", "address city"],
    "address": ["address", "street", "street address"],
    "resume": ["resume", "cv", "upload resume", "attach resume", "resume/cv"],
    "cover_letter": ["cover letter", "coverletter", "motivation letter"],
    "salary": ["salary", "expected salary", "compensation", "desired salary", "pay expectation"],
    "work_auth": ["authorized", "work authorization", "legally authorized", "sponsorship", "visa"],
    "years_experience": ["years of experience", "years experience", "experience years"],
    "current_company": ["current company", "employer", "company name"],
    "current_title": ["current title", "job title", "current role"],
}


def detect_ats(url: str) -> str:
    url_l = (url or "").lower()
    for ats, patterns in ATS_PATTERNS.items():
        if any(re.search(p, url_l) for p in patterns):
            return ats
    return "generic"


def _split_name(full_name: str) -> tuple[str, str]:
    parts = (full_name or "").strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def build_applicant_payload(
    user: User,
    profile: Optional[UserProfile],
    cv: Optional[CV],
) -> Dict[str, Any]:
    first = (profile.first_name if profile else None) or ""
    last = (profile.last_name if profile else None) or ""
    if cv and cv.full_name and (not first or not last):
        f2, l2 = _split_name(cv.full_name)
        first = first or f2
        last = last or l2

    phone = (cv.phone if cv else None) or ""
    linkedin = (cv.linkedin_url if cv else None) or ""
    portfolio = (cv.portfolio_url if cv else None) or ""
    location = (cv.location if cv else None) or (profile.location if profile else None) or ""
    email = (cv.email if cv else None) or user.email
    full_name = f"{first} {last}".strip() or (cv.full_name if cv else "") or user.email.split("@")[0]

    skills = []
    if cv and cv.skills:
        skills = cv.skills if isinstance(cv.skills, list) else []
    elif profile and profile.skills:
        skills = [s.name for s in profile.skills]

    return {
        "first_name": first,
        "last_name": last,
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "portfolio": portfolio,
        "location": location,
        "current_title": (profile.current_title if profile else None) or "",
        "current_company": (profile.current_company if profile else None) or "",
        "years_experience": (profile.years_of_experience if profile else None),
        "min_salary": (profile.min_salary if profile else None),
        "max_salary": (profile.max_salary if profile else None),
        "summary": (cv.summary if cv else None) or (profile.resume_text if profile else None) or "",
        "skills": skills,
        "experience": (cv.experience if cv else None) or [],
        "education": (cv.education if cv else None) or [],
        "work_auth": True,
        "needs_sponsorship": False,
        "cv_id": cv.id if cv else None,
        "cv_download_url": f"/api/v1/cvs/{cv.id}/pdf" if cv else None,
        "cv_html_export_url": f"/api/v1/cvs/{cv.id}/export" if cv else None,
    }


def map_field_key(label: str) -> Optional[str]:
    label_n = re.sub(r"\s+", " ", (label or "").strip().lower())
    for key, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias in label_n or label_n in alias:
                return key
    return None


def value_for_key(payload: Dict[str, Any], key: str) -> Any:
    if key == "salary":
        if payload.get("min_salary") and payload.get("max_salary"):
            return f"{payload['min_salary']}-{payload['max_salary']}"
        return payload.get("max_salary") or payload.get("min_salary") or ""
    if key == "work_auth":
        return "Yes" if payload.get("work_auth") else "No"
    if key == "years_experience":
        y = payload.get("years_experience")
        return str(int(y)) if y is not None else ""
    if key == "resume":
        return payload.get("cv_download_url")
    return payload.get(key, "")


async def answer_open_ended(
    question: str,
    payload: Dict[str, Any],
    job: Optional[Job] = None,
    *,
    db: Optional[Session] = None,
    user_id: Optional[int] = None,
) -> str:
    """Answer open-ended application questions in the applicant's voice."""
    question = (question or "").strip()
    if not question:
        return ""

    # Answer bank hit (learned from prior applications / user edits)
    if db is not None and user_id:
        try:
            from app.services.answer_bank import lookup_answer

            saved = lookup_answer(db, user_id, question)
            if saved:
                return saved
        except Exception as exc:
            logger.warning("answer bank lookup failed: %s", exc)

    # Heuristic answers without LLM
    q = question.lower()
    if "why" in q and ("company" in q or "us" in q or "role" in q or "interested" in q):
        company = job.company if job else "your company"
        title = job.title if job else "this role"
        skills = ", ".join((payload.get("skills") or [])[:5]) or "my background"
        return (
            f"I'm excited about {title} at {company}. "
            f"My experience with {skills} aligns closely with what you're building, "
            f"and I'm motivated to contribute immediately while growing with the team."
        )
    if "tell us about yourself" in q or "about you" in q:
        return (payload.get("summary") or "").strip() or (
            f"I'm {payload.get('full_name')}, currently {payload.get('current_title') or 'a professional'} "
            f"with experience across {(payload.get('skills') or ['relevant domains'])[:3]}."
        )
    if "salary" in q or "compensation" in q:
        return str(value_for_key(payload, "salary") or "Negotiable based on total package")
    if "sponsor" in q or "visa" in q:
        return "No" if not payload.get("needs_sponsorship") else "Yes"
    if "authorized" in q or "legally" in q:
        return "Yes" if payload.get("work_auth") else "No"

    # Optional LLM path
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            context = {
                "name": payload.get("full_name"),
                "summary": (payload.get("summary") or "")[:800],
                "skills": payload.get("skills"),
                "job_title": job.title if job else None,
                "company": job.company if job else None,
            }
            resp = client.chat.completions.create(
                model=getattr(settings, "LLM_MODEL", "gpt-4-turbo-preview"),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You write concise, first-person answers for job applications. "
                            "Sound natural and specific. 2-5 sentences max. No markdown."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Applicant context: {json.dumps(context)}\nQuestion: {question}",
                    },
                ],
                temperature=0.5,
                max_tokens=220,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as exc:
            logger.warning("LLM open-ended answer failed: %s", exc)

    return (
        f"Based on my experience as {payload.get('current_title') or 'a candidate'}, "
        f"I bring relevant skills ({', '.join((payload.get('skills') or [])[:4]) or 'strong fundamentals'}) "
        f"and a track record of delivering results. Happy to expand in an interview."
    )


def build_fill_plan(payload: Dict[str, Any], ats: str) -> Dict[str, Any]:
    """Declarative fill plan the extension / Playwright worker executes."""
    common_fields = [
        {"key": "first_name", "strategies": ["name", "label", "placeholder", "autocomplete"], "type": "text"},
        {"key": "last_name", "strategies": ["name", "label", "placeholder", "autocomplete"], "type": "text"},
        {"key": "full_name", "strategies": ["name", "label", "placeholder"], "type": "text"},
        {"key": "email", "strategies": ["name", "label", "placeholder", "autocomplete", "type=email"], "type": "email"},
        {"key": "phone", "strategies": ["name", "label", "placeholder", "type=tel"], "type": "tel"},
        {"key": "linkedin", "strategies": ["name", "label", "placeholder"], "type": "url"},
        {"key": "portfolio", "strategies": ["name", "label", "placeholder"], "type": "url"},
        {"key": "location", "strategies": ["name", "label", "placeholder"], "type": "text"},
        {"key": "current_company", "strategies": ["name", "label"], "type": "text"},
        {"key": "current_title", "strategies": ["name", "label"], "type": "text"},
        {"key": "resume", "strategies": ["file", "label"], "type": "file"},
        {"key": "cover_letter", "strategies": ["textarea", "label"], "type": "textarea"},
    ]

    multi_step = ats in ("workday", "workable", "greenhouse")
    return {
        "ats": ats,
        "multi_step": multi_step,
        "max_steps": 6 if ats == "workday" else 4,
        "auto_submit": False,  # user confirm by default; headless can override
        "field_types_supported": [
            "text", "email", "tel", "url", "textarea", "select", "radio",
            "checkbox", "file", "number", "date", "open_ended",
        ],
        "fields": [
            {**f, "value": value_for_key(payload, f["key"])}
            for f in common_fields
            if value_for_key(payload, f["key"]) not in (None, "")
        ],
        "boolean_defaults": {
            "work_authorization": True,
            "sponsorship": False,
            "relocate": bool(payload.get("relocate")) if "relocate" in payload else False,
            "remote_ok": True,
        },
        "next_button_selectors": [
            "button:has-text('Next')",
            "button:has-text('Continue')",
            "button:has-text('Save and Continue')",
            "[data-automation-id='bottom-navigation-next-button']",  # Workday
        ],
        "submit_button_selectors": [
            "button:has-text('Submit application')",
            "button:has-text('Submit Application')",
            "#submit_app",
            "button[type='submit']",
            "input[type='submit']",
            "button.application-button",
        ],
        "captcha_selectors": [
            "iframe[src*='recaptcha']",
            "iframe[src*='hcaptcha']",
            ".g-recaptcha",
            "[data-sitekey]",
        ],
    }


def build_apply_package(
    db: Session,
    user: User,
    job: Job,
    application: Optional[Application] = None,
    cv: Optional[CV] = None,
) -> Dict[str, Any]:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not cv:
        cv_id = application.cv_id if application else None
        if cv_id:
            cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == user.id).first()
        if not cv:
            cv = (
                db.query(CV)
                .filter(CV.user_id == user.id)
                .order_by(CV.is_primary.desc(), CV.created_at.desc())
                .first()
            )

    payload = build_applicant_payload(user, profile, cv)
    # Materialize resume path for headless + expose download URL for extension
    try:
        from app.services.resume_files import ensure_resume_local_path

        ensure_resume_local_path(user.id, payload, cv)
    except Exception as exc:
        logger.warning("resume materialize failed: %s", exc)

    from app.services.ats_adapters.form_helpers import profile_completeness

    completeness = profile_completeness(payload)
    ats = detect_ats(job.external_url or "")
    plan = build_fill_plan(payload, ats)
    # Extension may genuinely submit when user opted in
    plan["auto_submit"] = bool(getattr(user, "auto_apply_submit", False))
    plan["genuine_submit"] = bool(getattr(user, "auto_apply_submit", False))

    return {
        "application_id": application.id if application else None,
        "job_id": job.id,
        "job_url": job.external_url,
        "job_title": job.title,
        "company": job.company,
        "ats": ats,
        "applicant": payload,
        "fill_plan": plan,
        "profile_completeness": completeness,
        "capabilities": {
            "text": True,
            "select": True,
            "radio": True,
            "checkbox": True,
            "file": True,
            "multi_step": True,
            "open_ended": True,
            "captcha": bool(
                getattr(settings, "CAPTCHA_MOCK", False)
                or getattr(settings, "TWOCAPTCHA_API_KEY", None)
            ),
            "headless": True,
            "genuine_submit": bool(getattr(user, "auto_apply_submit", False)),
        },
    }
