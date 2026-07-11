"""
Job Enrichment Service

Takes a raw job (title + description + whatever the scraper gave us) and extracts
structured fields that the 1:1 matcher can filter on:

  - skills_required      (from a curated skill dictionary)
  - experience_years_min (regex: "X+ years", "minimum X years")
  - experience_years_max
  - visa_sponsorship     (keyword detection: "visa", "sponsorship", "relocate")
  - remote/hybrid        (already detected by most scrapers — normalized here)
  - seniority            (already parsed by scrapers — normalized + title-based fallback)
  - employment_type      (normalized from "FULL_TIME" etc.)
  - salary_min/max       (parse from description if scraper didn't)
  - industry             (from company directory + keyword detection)
  - company_size         (from company directory)
  - benefits_extracted   (keyword detection: "health", "equity", "pension", ...)

Called by the aggregator after scraping, before saving. Also exposed via
POST /jobs/{id}/enrich for re-enrichment on demand.
"""

import re
from typing import List, Dict, Optional, Any
from app.services.cv_tailor import SKILL_DICTIONARY  # reuse the same skill dict


# Visa / sponsorship keywords
VISA_KEYWORDS = [
    "visa sponsorship", "sponsorship available", "will sponsor", "offer sponsorship",
    "relocation assistance", "relocation support", "relocate", "relocation package",
    "willing to sponsor", "visa support", "work visa", "h1b", "tier 2", "tier 5",
    "skilled worker visa", "we can sponsor",
]
NO_VISA_KEYWORDS = [
    "no sponsorship", "cannot sponsor", "can't sponsor", "no visa sponsorship",
    "must be authorized", "must have work authorization", "no relocation",
    "unable to sponsor", "not offering sponsorship",
]

# Benefits keywords — maps to normalized benefit names
BENEFITS_MAP = {
    "health insurance": "Health insurance", "medical insurance": "Health insurance",
    "dental": "Dental", "vision": "Vision",
    "401k": "401(k)", "pension": "Pension", "retirement": "Retirement plan",
    "equity": "Equity", "stock options": "Equity", "options": "Equity",
    "unlimited pto": "Unlimited PTO", "unlimited vacation": "Unlimited PTO",
    "flexible vacation": "Flexible PTO", "flexible pto": "Flexible PTO",
    "remote stipend": "Remote stipend", "home office stipend": "Remote stipend",
    "learning budget": "Learning budget", "learning stipend": "Learning budget",
    "education budget": "Learning budget", "professional development": "Learning budget",
    "gym": "Gym/wellness", "wellness stipend": "Gym/wellness", "wellness budget": "Gym/wellness",
    "parental leave": "Parental leave", "maternity": "Parental leave", "paternity": "Parental leave",
    "sabbatical": "Sabbatical",
    "commuter": "Commuter benefits", "transport": "Commuter benefits",
    "free lunch": "Meals", "free food": "Meals", "catered lunch": "Meals",
    "mental health": "Mental health support",
}

# Industry keywords — maps company/job text to an industry
INDUSTRY_KEYWORDS = {
    "fintech": ["fintech", "financial", "banking", "payments", "payment", "stripe", "plaid", "mercury"],
    "crypto": ["crypto", "blockchain", "web3", "ethereum", "bitcoin", "defi", "nft"],
    "ai/ml": ["ai", "machine learning", "ml", "deep learning", "llm", "gpt", "artificial intelligence", "neural"],
    "saas": ["saas", "software as a service", "b2b", "cloud software"],
    "e-commerce": ["e-commerce", "ecommerce", "retail", "marketplace", "shopify"],
    "devtools": ["devtools", "developer tools", "infrastructure", "ci/cd", "ide", "sdk"],
    "healthtech": ["healthtech", "health tech", "medical", "healthcare", "biotech", "telemedicine"],
    "edtech": ["edtech", "education", "learning", "course", "student"],
    "gaming": ["gaming", "game", "esports"],
    "media": ["media", "news", "content", "publishing", "streaming"],
    "travel": ["travel", "hospitality", "hotel", "booking"],
    "cybersecurity": ["security", "cybersecurity", "infosec", "pentest", "vulnerability"],
}


def _extract_skills(text: str) -> List[str]:
    """Extract skills from text using the curated skill dictionary."""
    if not text:
        return []
    text_lower = text.lower()
    found = []
    seen = set()
    for skill in SKILL_DICTIONARY:
        if skill in seen:
            continue
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
            seen.add(skill)
    return found


def _extract_experience_years(text: str) -> tuple[Optional[float], Optional[float]]:
    """Extract min/max years of experience from text.

    Patterns: "5+ years", "3-5 years", "minimum 5 years", "at least 5 years",
    "5 years of experience".
    """
    if not text:
        return None, None
    text_lower = text.lower()

    # Range: "3-5 years", "3 to 5 years"
    range_match = re.search(r'(\d+(?:\.\d+)?)\s*[-–to]+\s*(\d+(?:\.\d+)?)\s*\+?\s*years?', text_lower)
    if range_match:
        min_y = float(range_match.group(1))
        max_y = float(range_match.group(2))
        return min_y, max_y

    # "5+ years", "5 + years"
    plus_match = re.search(r'(\d+(?:\.\d+)?)\s*\+\s*years?', text_lower)
    if plus_match:
        min_y = float(plus_match.group(1))
        return min_y, None

    # "minimum 5 years", "at least 5 years", "5 years of experience"
    min_match = re.search(r'(?:minimum|at least|min\.)\s*(\d+(?:\.\d+)?)\s*\+?\s*years?', text_lower)
    if min_match:
        return float(min_match.group(1)), None

    plain_match = re.search(r'(\d+(?:\.\d+)?)\s*years?\s+(?:of\s+)?(?:experience|exp)', text_lower)
    if plain_match:
        return float(plain_match.group(1)), None

    return None, None


def _detect_visa_sponsorship(text: str) -> Optional[bool]:
    """Detect whether the job offers visa sponsorship.

    Returns True (offers), False (no sponsorship), or None (unknown).
    """
    if not text:
        return None
    text_lower = text.lower()
    # Check "no sponsorship" first — it's more specific
    for kw in NO_VISA_KEYWORDS:
        if kw in text_lower:
            return False
    for kw in VISA_KEYWORDS:
        if kw in text_lower:
            return True
    return None


def _detect_remote_policy(text: str, existing_remote: bool, existing_hybrid: bool) -> Dict[str, bool]:
    """Normalize remote/hybrid detection from text + existing scraper values."""
    if not text:
        return {"remote": existing_remote, "hybrid": existing_hybrid}
    text_lower = text.lower()
    remote = existing_remote
    hybrid = existing_hybrid
    # Reinforce from text
    if "remote" in text_lower or "work from home" in text_lower or "wfh" in text_lower:
        remote = True
    if "hybrid" in text_lower:
        hybrid = True
    # "on-site" / "in-office" means not remote
    if "on-site" in text_lower or "in-office" in text_lower or "on site" in text_lower:
        # Only override if neither was set
        if not remote and not hybrid:
            remote = False
            hybrid = False
    return {"remote": remote, "hybrid": hybrid}


def _normalize_seniority(title: str, existing: Optional[str]) -> Optional[str]:
    """Normalize seniority from title + existing value."""
    if existing:
        return existing.lower()
    if not title:
        return "mid"
    return _parse_seniority_from_title(title)


def _parse_seniority_from_title(title: str) -> str:
    """Parse seniority level from a job title."""
    if not title:
        return "mid"
    t = title.lower()
    if any(x in t for x in ["executive", "c-level", "cto", "ceo", "cfo", "chief", "vp", "vice president"]):
        return "executive"
    if any(x in t for x in ["director", "head of"]):
        return "director"
    if any(x in t for x in ["lead", "principal", "staff"]):
        return "lead"
    if any(x in t for x in ["senior", "sr.", "sr ", "snr"]):
        return "senior"
    if any(x in t for x in ["junior", "jr.", "jr ", "entry", "graduate", "intern"]):
        return "entry"
    return "mid"


def _normalize_employment_type(text: str, existing: Optional[str]) -> Optional[str]:
    """Normalize employment type."""
    if existing:
        e = existing.lower().replace("-", "").replace("_", "").replace(" ", "")
        mapping = {
            "fulltime": "full_time", "full": "full_time",
            "parttime": "part_time", "part": "part_time",
            "contract": "contract", "contractor": "contract",
            "intern": "internship", "internship": "internship",
            "temporary": "temporary", "temp": "temporary",
        }
        return mapping.get(e, existing.lower())
    if not text:
        return None
    t = text.lower()
    if "full-time" in t or "full time" in t:
        return "full_time"
    if "part-time" in t or "part time" in t:
        return "part_time"
    if "contract" in t:
        return "contract"
    if "intern" in t:
        return "internship"
    return None


def _parse_salary_from_text(text: str) -> tuple[Optional[int], Optional[int]]:
    """Parse salary range from description text.

    Handles: "$80,000 - $120,000", "£80k-£120k", "$80k - $120k per year",
    "80,000 - 120,000 GBP".
    """
    if not text:
        return None, None
    # Find currency + number patterns
    # Pattern: currency symbol + number (with optional k) - currency symbol + number
    patterns = [
        r'[£$€]\s*(\d+(?:\.\d+)?)\s*k?\s*[-–to]+\s*[£$€]?\s*(\d+(?:\.\d+)?)\s*k?',
        r'[£$€]\s*(\d+(?:,\d{3})*)\s*[-–to]+\s*[£$€]?\s*(\d+(?:,\d{3})*)',
        r'(\d+(?:\.\d+)?)\s*k\s*[-–to]+\s*(\d+(?:\.\d+)?)\s*k',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                low = float(match.group(1).replace(",", ""))
                high = float(match.group(2).replace(",", ""))
                # If the number has "k" suffix or is < 1000, multiply by 1000
                if low < 1000:
                    low *= 1000
                if high < 1000:
                    high *= 1000
                if low > high:
                    low, high = high, low
                return int(low), int(high)
            except (ValueError, IndexError):
                continue
    return None, None


def _extract_benefits(text: str) -> List[str]:
    """Extract benefits from text."""
    if not text:
        return []
    text_lower = text.lower()
    found = set()
    for kw, label in BENEFITS_MAP.items():
        if kw in text_lower:
            found.add(label)
    return sorted(found)


def _detect_industry(text: str, company: str) -> Optional[str]:
    """Detect industry from job text + company name."""
    if not text and not company:
        return None
    combined = f"{company or ''} {text or ''}".lower()
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            return industry
    return None


def _lookup_company_metadata(company: str) -> Dict[str, Optional[str]]:
    """Look up industry + size from the company directory."""
    if not company:
        return {"industry": None, "company_size": None}
    try:
        from app.scrapers.companies import get_company_atss
        info = get_company_atss(company)
        if info:
            return {"industry": info.get("industry"), "company_size": info.get("size")}
    except Exception:
        pass
    return {"industry": None, "company_size": None}


def enrich_job(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich a raw job dict with structured fields extracted from its description.

    Args:
        job_data: dict with at least title, company, description. May also have
            remote, hybrid, seniority, employment_type, min_salary, max_salary,
            skills_required, experience_years_min/max from the scraper.

    Returns:
        The same dict with enriched fields populated:
            skills_required, experience_years_min/max, visa_sponsorship,
            remote, hybrid, seniority, employment_type, min_salary, max_salary,
            industry, company_size, benefits_extracted
    """
    if not job_data:
        return job_data

    title = job_data.get("title") or ""
    company = job_data.get("company") or ""
    description = job_data.get("description") or ""
    full_text = f"{title} {company} {description}"

    # 1. Skills (merge scraper-provided + extracted)
    existing_skills = job_data.get("skills_required") or []
    extracted_skills = _extract_skills(full_text)
    all_skills = list({s for s in (existing_skills + extracted_skills)})
    job_data["skills_required"] = all_skills

    # 2. Experience years (always set the keys, even if None)
    exp_min, exp_max = _extract_experience_years(full_text)
    if exp_min is not None and not job_data.get("experience_years_min"):
        job_data["experience_years_min"] = exp_min
    elif not job_data.get("experience_years_min"):
        job_data["experience_years_min"] = None
    if exp_max is not None and not job_data.get("experience_years_max"):
        job_data["experience_years_max"] = exp_max
    elif not job_data.get("experience_years_max"):
        job_data["experience_years_max"] = None

    # 3. Visa sponsorship (always set, even if None = unknown)
    if job_data.get("visa_sponsorship") is None:
        job_data["visa_sponsorship"] = _detect_visa_sponsorship(full_text)

    # 4. Remote / hybrid
    remote_policy = _detect_remote_policy(
        full_text,
        job_data.get("remote", False),
        job_data.get("hybrid", False),
    )
    job_data["remote"] = remote_policy["remote"]
    job_data["hybrid"] = remote_policy["hybrid"]

    # 5. Seniority
    job_data["seniority"] = _normalize_seniority(title, job_data.get("seniority"))

    # 6. Employment type
    if not job_data.get("employment_type"):
        job_data["employment_type"] = _normalize_employment_type(full_text, None)

    # 7. Salary — parse from description if scraper didn't provide
    if not job_data.get("min_salary") and not job_data.get("max_salary"):
        sal_min, sal_max = _parse_salary_from_text(full_text)
        if sal_min:
            job_data["min_salary"] = sal_min
        if sal_max:
            job_data["max_salary"] = sal_max

    # 8. Benefits
    job_data["benefits_extracted"] = _extract_benefits(full_text)

    # 9. Industry + company size (from directory + text detection)
    company_meta = _lookup_company_metadata(company)
    if not job_data.get("industry"):
        job_data["industry"] = company_meta["industry"] or _detect_industry(description, company)
    if not job_data.get("company_size"):
        job_data["company_size"] = company_meta["company_size"]

    return job_data


class JobEnricher:
    """Class wrapper for the enrich function."""

    def enrich(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        return enrich_job(job_data)


job_enricher = JobEnricher()