"""
Materialize a local resume file for Playwright headless apply.

Writes under /tmp/jobscale_resumes/. Plain text (.txt) or HTML named .pdf
is acceptable for testing when a real PDF is unavailable.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, Optional

RESUME_DIR = "/tmp/jobscale_resumes"


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", (value or "user").strip())[:48]
    return slug or "user"


def _format_resume_text(applicant: Dict[str, Any], cv: Any = None) -> str:
    name = (getattr(cv, "full_name", None) if cv else None) or applicant.get("full_name") or "Applicant"
    email = (getattr(cv, "email", None) if cv else None) or applicant.get("email") or ""
    phone = (getattr(cv, "phone", None) if cv else None) or applicant.get("phone") or ""
    location = (getattr(cv, "location", None) if cv else None) or applicant.get("location") or ""
    linkedin = (getattr(cv, "linkedin_url", None) if cv else None) or applicant.get("linkedin") or ""
    summary = (getattr(cv, "summary", None) if cv else None) or applicant.get("summary") or ""
    skills = (getattr(cv, "skills", None) if cv else None) or applicant.get("skills") or []
    experience = (getattr(cv, "experience", None) if cv else None) or applicant.get("experience") or []
    education = (getattr(cv, "education", None) if cv else None) or applicant.get("education") or []

    lines = [
        name,
        email,
        phone,
        location,
        linkedin,
        "",
        "SUMMARY",
        summary or f"{applicant.get('current_title') or 'Professional'} seeking new opportunities.",
        "",
        "SKILLS",
        ", ".join(skills) if isinstance(skills, list) else str(skills or ""),
        "",
        "EXPERIENCE",
    ]
    if isinstance(experience, list):
        for exp in experience[:8]:
            if not isinstance(exp, dict):
                lines.append(str(exp))
                continue
            role = exp.get("role") or exp.get("title") or ""
            company = exp.get("company") or ""
            dates = " – ".join(filter(None, [exp.get("start_date"), exp.get("end_date") or "Present"]))
            lines.append(f"{role} @ {company} ({dates})".strip())
            if exp.get("description"):
                lines.append(str(exp["description"])[:600])
    else:
        lines.append(str(experience or ""))

    lines.extend(["", "EDUCATION"])
    if isinstance(education, list):
        for edu in education[:6]:
            if not isinstance(edu, dict):
                lines.append(str(edu))
                continue
            lines.append(
                f"{edu.get('degree', '')} {edu.get('field', '')} — "
                f"{edu.get('institution', '')} ({edu.get('graduation_year', '')})".strip()
            )
    else:
        lines.append(str(education or ""))

    return "\n".join(line for line in lines if line is not None)


def write_resume_file(
    user_id: int,
    applicant: Dict[str, Any],
    cv: Any = None,
    *,
    as_pdf_name: bool = True,
) -> str:
    """
    Write a temp resume for headless upload and return the local path.

    Prefer an existing local CV file_path when present; otherwise generate
    a text/HTML resume (optionally named .pdf for ATS file inputs).
    """
    os.makedirs(RESUME_DIR, exist_ok=True)

    existing = getattr(cv, "file_path", None) if cv else None
    if existing and os.path.isfile(existing):
        return existing

    cv_id = getattr(cv, "id", None) if cv else applicant.get("cv_id") or "na"
    slug = _safe_slug(str(applicant.get("full_name") or f"user_{user_id}"))
    ext = ".pdf" if as_pdf_name else ".txt"
    path = os.path.join(RESUME_DIR, f"user_{user_id}_cv_{cv_id}_{slug}{ext}")

    body = _format_resume_text(applicant, cv)
    if as_pdf_name:
        # HTML content with .pdf extension is enough for Playwright set_input_files tests
        html = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<title>{slug} Resume</title></head><body><pre>"
            f"{body.replace('&', '&amp;').replace('<', '&lt;')}"
            "</pre></body></html>"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)

    return path


def ensure_resume_local_path(
    user_id: int,
    applicant: Dict[str, Any],
    cv: Any = None,
) -> Optional[str]:
    """Return applicant['resume_local_path'], creating the file if missing."""
    existing = applicant.get("resume_local_path")
    if existing and os.path.isfile(str(existing)):
        return str(existing)
    path = write_resume_file(user_id, applicant, cv)
    applicant["resume_local_path"] = path
    return path
