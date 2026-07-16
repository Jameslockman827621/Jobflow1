"""
Materialize a local resume file for Playwright headless apply.

Writes under /tmp/jobscale_resumes/. Generates a real minimal PDF so ATS
file validators accept the upload (not HTML disguised as .pdf).
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


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_minimal_pdf(text: str) -> bytes:
    """
    Build a valid single-page PDF with Helvetica text lines.
    No external deps — ATS validators accept application/pdf magic + structure.
    """
    lines = [ln[:110] for ln in (text or "Resume").splitlines() if ln is not None][:60]
    if not lines:
        lines = ["Resume"]

    y_start = 750
    content_ops = ["BT", "/F1 11 Tf", "14 TL", f"50 {y_start} Td"]
    for i, line in enumerate(lines):
        esc = _pdf_escape(line)
        if i == 0:
            content_ops.append(f"({esc}) Tj")
        else:
            content_ops.append("T*")
            content_ops.append(f"({esc}) Tj")
    content_ops.append("ET")
    stream = "\n".join(content_ops).encode("latin-1", errors="replace")

    objects: list[bytes] = []
    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objects.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
    objects.append(
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj\n"
    )
    objects.append(
        f"4 0 obj<< /Length {len(stream)} >>stream\n".encode("ascii")
        + stream
        + b"\nendstream\nendobj\n"
    )
    objects.append(b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n")

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(out))
        out.extend(obj)

    xref_pos = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    out.extend(
        f"trailer<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n".encode("ascii")
    )
    return bytes(out)


def is_real_pdf(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            head = f.read(5)
        return head == b"%PDF-"
    except Exception:
        return False


def write_resume_file(
    user_id: int,
    applicant: Dict[str, Any],
    cv: Any = None,
    *,
    as_pdf_name: bool = True,
) -> str:
    """
    Write a temp resume for headless upload and return the local path.

    Prefer an existing local CV file_path when present and valid;
    otherwise generate a real minimal PDF (or .txt when as_pdf_name=False).
    """
    os.makedirs(RESUME_DIR, exist_ok=True)

    existing = getattr(cv, "file_path", None) if cv else None
    if existing and os.path.isfile(existing):
        # Re-wrap non-PDF uploads as PDF for ATS accept filters
        if existing.lower().endswith(".pdf") and is_real_pdf(existing):
            return existing
        # If it's a real PDF with wrong extension, still use it
        if is_real_pdf(existing):
            return existing

    cv_id = getattr(cv, "id", None) if cv else applicant.get("cv_id") or "na"
    slug = _safe_slug(str(applicant.get("full_name") or f"user_{user_id}"))
    ext = ".pdf" if as_pdf_name else ".txt"
    path = os.path.join(RESUME_DIR, f"user_{user_id}_cv_{cv_id}_{slug}{ext}")

    body = _format_resume_text(applicant, cv)
    if as_pdf_name:
        pdf_bytes = build_minimal_pdf(body)
        with open(path, "wb") as f:
            f.write(pdf_bytes)
        applicant["resume_is_pdf"] = True
        applicant["resume_mime"] = "application/pdf"
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        applicant["resume_is_pdf"] = False
        applicant["resume_mime"] = "text/plain"

    return path


def ensure_resume_local_path(
    user_id: int,
    applicant: Dict[str, Any],
    cv: Any = None,
) -> Optional[str]:
    """Return applicant['resume_local_path'], creating the file if missing."""
    existing = applicant.get("resume_local_path")
    if existing and os.path.isfile(str(existing)):
        # Upgrade fake HTML-.pdf from older runs
        if str(existing).lower().endswith(".pdf") and not is_real_pdf(str(existing)):
            path = write_resume_file(user_id, applicant, cv)
            applicant["resume_local_path"] = path
            return path
        return str(existing)
    path = write_resume_file(user_id, applicant, cv)
    applicant["resume_local_path"] = path
    return path
