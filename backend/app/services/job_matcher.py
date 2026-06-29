"""
1:1 Job Matching Service

World-class matching: the user tells us their top 5 must-haves (e.g. salary ≥ £80k,
remote only, Python required, visa sponsorship, senior level). We filter jobs to
only those that satisfy ALL must-haves, then rank them by how many additional
ranked priorities they meet.

Each job returns a transparent breakdown:
  [
    {"field": "salary_min", "label": "Salary ≥ £80k", "required": true, "met": true, "job_value": "£90,000"},
    {"field": "remote", "label": "Remote", "required": true, "met": true, "job_value": "Yes"},
    {"field": "skills", "label": "Python", "required": true, "met": true, "job_value": "Has Python"},
    {"field": "visa_sponsorship", "label": "Visa sponsorship", "required": true, "met": false, "job_value": "Not mentioned"},
    {"field": "seniority", "label": "Senior level", "required": true, "met": true, "job_value": "Senior"},
  ]

No fluff, no guessing — if the user said they want X, we only show jobs that have X.
"""

from typing import List, Dict, Optional, Any, Tuple


# The dimensions we support for must-haves. Each has a label, a way to check
# whether a job meets it, and a way to format the job's value for display.
PRIORITY_DIMENSIONS = {
    "salary_min": {
        "label": "Minimum salary",
        "input_type": "number",
        "unit": "£",
        "description": "Only show jobs paying at least this amount",
    },
    "remote": {
        "label": "Remote-friendly",
        "input_type": "boolean",
        "description": "Only show remote or hybrid jobs",
    },
    "remote_only": {
        "label": "Fully remote only",
        "input_type": "boolean",
        "description": "Only show 100% remote jobs (no hybrid)",
    },
    "location": {
        "label": "Location",
        "input_type": "text",
        "description": "Only show jobs in this city/country",
    },
    "seniority": {
        "label": "Seniority level",
        "input_type": "multiselect",
        "options": ["entry", "mid", "senior", "lead", "director", "executive"],
        "description": "Only show jobs at these seniority levels",
    },
    "employment_type": {
        "label": "Employment type",
        "input_type": "multiselect",
        "options": ["full_time", "part_time", "contract", "internship", "temporary"],
        "description": "Only show full-time / contract / etc.",
    },
    "skills": {
        "label": "Required skills",
        "input_type": "skills",
        "description": "Only show jobs that list these skills",
    },
    "visa_sponsorship": {
        "label": "Visa sponsorship",
        "input_type": "boolean",
        "description": "Only show jobs that offer visa sponsorship / relocation",
    },
    "experience_max": {
        "label": "Max years of experience required",
        "input_type": "number",
        "description": "Only show jobs asking for at most this many years",
    },
    "company_size": {
        "label": "Company size",
        "input_type": "multiselect",
        "options": ["startup", "mid", "enterprise"],
        "description": "Only show companies of this size",
    },
    "industry": {
        "label": "Industry",
        "input_type": "multiselect",
        "options": ["fintech", "crypto", "ai/ml", "saas", "e-commerce", "devtools", "healthtech", "edtech", "gaming", "media", "travel", "cybersecurity"],
        "description": "Only show jobs in these industries",
    },
    "company": {
        "label": "Target company",
        "input_type": "text",
        "description": "Only show jobs at this company",
    },
}


def _check_must_have(field: str, required_value: Any, job: Dict) -> Tuple[bool, str]:
    """Check whether a job meets a single must-have.

    Returns (met, job_value_description).
    """
    if field == "salary_min":
        job_max = job.get("max_salary")
        job_min = job.get("min_salary")
        # Job meets if either its max or min salary >= required
        if job_max is not None and job_max >= required_value:
            return True, f"£{job_max:,}/yr" if job_max else "Yes"
        if job_min is not None and job_min >= required_value:
            return True, f"£{job_min:,}/yr"
        if job_max is None and job_min is None:
            return False, "Salary not listed"
        return False, f"£{job_max or job_min:,}/yr"

    if field == "remote":
        if job.get("remote") or job.get("hybrid"):
            label = "Remote" if job.get("remote") and not job.get("hybrid") else "Hybrid" if job.get("hybrid") else "Yes"
            return True, label
        return False, "On-site"

    if field == "remote_only":
        if job.get("remote") and not job.get("hybrid"):
            return True, "Fully remote"
        if job.get("hybrid"):
            return False, "Hybrid (not fully remote)"
        return False, "On-site"

    if field == "location":
        job_loc = (job.get("location") or "").lower()
        req_loc = str(required_value).lower()
        if req_loc in job_loc:
            return True, job.get("location") or "Match"
        return False, job.get("location") or "Not specified"

    if field == "seniority":
        job_sen = (job.get("seniority") or "").lower()
        required_levels = [s.lower() for s in (required_value if isinstance(required_value, list) else [required_value])]
        if job_sen in required_levels:
            return True, job_sen.title()
        return False, (job.get("seniority") or "Unknown").title()

    if field == "employment_type":
        job_type = (job.get("employment_type") or "").lower().replace("-", "_")
        required_types = [t.lower().replace("-", "_") for t in (required_value if isinstance(required_value, list) else [required_value])]
        if job_type in required_types:
            return True, job_type.replace("_", " ").title()
        return False, (job.get("employment_type") or "Unknown").replace("_", " ").title()

    if field == "skills":
        job_skills = [s.lower() for s in (job.get("skills_required") or [])]
        required_skills = [s.lower() for s in (required_value if isinstance(required_value, list) else [required_value])]
        matched = [s for s in required_skills if any(s in js or js in s for js in job_skills)]
        missing = [s for s in required_skills if s not in matched]
        if not missing:
            return True, f"Has all {len(required_skills)}"
        if matched:
            return False, f"Has {len(matched)}/{len(required_skills)}"
        return False, "None listed"

    if field == "visa_sponsorship":
        visa = job.get("visa_sponsorship")
        if visa is True:
            return True, "Offers sponsorship"
        if visa is False:
            return False, "No sponsorship"
        return False, "Not mentioned"

    if field == "experience_max":
        job_exp_max = job.get("experience_years_max")
        job_exp_min = job.get("experience_years_min")
        # Job meets if its max required experience <= required_value
        if job_exp_max is not None and job_exp_max <= required_value:
            return True, f"{int(job_exp_max)} yrs max"
        if job_exp_min is not None and job_exp_min <= required_value:
            return True, f"{int(job_exp_min)}+ yrs"
        if job_exp_max is None and job_exp_min is None:
            return False, "Not specified"
        return False, f"{int(job_exp_max or job_exp_min)} yrs"

    if field == "company_size":
        size = (job.get("company_size") or "").lower()
        required_sizes = [s.lower() for s in (required_value if isinstance(required_value, list) else [required_value])]
        if size in required_sizes:
            return True, size.title()
        return False, (job.get("company_size") or "Unknown").title()

    if field == "industry":
        industry = (job.get("industry") or "").lower()
        required_industries = [i.lower() for i in (required_value if isinstance(required_value, list) else [required_value])]
        if industry in required_industries:
            return True, industry.title()
        return False, (job.get("industry") or "Unknown").title()

    if field == "company":
        job_company = (job.get("company") or "").lower()
        req_company = str(required_value).lower()
        if req_company in job_company or job_company in req_company:
            return True, job.get("company") or "Match"
        return False, job.get("company") or "Different company"

    return False, "Unknown field"


def _label_for_must_have(field: str, value: Any) -> str:
    """Generate a human-readable label for a must-have."""
    dim = PRIORITY_DIMENSIONS.get(field, {})
    base_label = dim.get("label", field)
    if field == "salary_min":
        return f"Salary ≥ £{int(value):,}"
    if field == "remote":
        return "Remote or hybrid"
    if field == "remote_only":
        return "Fully remote"
    if field == "location":
        return f"Location: {value}"
    if field == "seniority":
        levels = value if isinstance(value, list) else [value]
        return f"Level: {', '.join(l.title() for l in levels)}"
    if field == "employment_type":
        types = value if isinstance(value, list) else [value]
        return f"Type: {', '.join(t.replace('_',' ').title() for t in types)}"
    if field == "skills":
        skills = value if isinstance(value, list) else [value]
        return f"Skills: {', '.join(skills[:3])}{'...' if len(skills) > 3 else ''}"
    if field == "visa_sponsorship":
        return "Visa sponsorship"
    if field == "experience_max":
        return f"Max {value} yrs experience"
    if field == "company_size":
        sizes = value if isinstance(value, list) else [value]
        return f"Company: {', '.join(s.title() for s in sizes)}"
    if field == "industry":
        inds = value if isinstance(value, list) else [value]
        return f"Industry: {', '.join(i.title() for i in inds)}"
    if field == "company":
        return f"Company: {value}"
    return base_label


def match_jobs(
    must_haves: List[Dict],
    priority_weights: Optional[List[Dict]],
    jobs: List[Dict],
) -> List[Dict]:
    """1:1 matching: filter jobs by ALL must-haves, score by ranked priorities.

    Args:
        must_haves: [{"field": "salary_min", "value": 80000}, ...] — jobs must
            satisfy ALL of these to be included.
        priority_weights: [{"field": "salary", "weight": 5}, ...] — used to rank
            jobs that pass the must-have filter. Higher weight = more important.
        jobs: list of job dicts (already enriched).

    Returns:
        List of jobs that meet ALL must-haves, sorted by weighted priority score
        (highest first). Each job gets a `match_breakdown` field showing every
        must-have and whether it's met, plus a `match_score` (0-100).
    """
    if not jobs:
        return []

    must_haves = must_haves or []
    priority_weights = priority_weights or []

    results = []
    for job in jobs:
        # Check every must-have
        breakdown = []
        all_met = True
        for mh in must_haves:
            field = mh.get("field")
            value = mh.get("value")
            met, job_value = _check_must_have(field, value, job)
            label = _label_for_must_have(field, value)
            breakdown.append({
                "field": field,
                "label": label,
                "required": True,
                "met": met,
                "job_value": job_value,
            })
            if not met:
                all_met = False

        if not all_met:
            continue  # Hard filter — job doesn't meet a must-have, skip it

        # Score: start at 100, subtract for missing priority_weights (soft prefs)
        score = 100
        weighted_total = 0
        weighted_met = 0
        for pw in priority_weights:
            field = pw.get("field")
            weight = pw.get("weight", 1)
            # If this priority is also a must-have, it's already met (we passed the filter)
            is_must_have = any(mh.get("field") == field for mh in must_haves)
            if is_must_have:
                weighted_total += weight
                weighted_met += weight
                continue
            # Otherwise it's a soft preference — check if met
            value = pw.get("value", True)
            met, _ = _check_must_have(field, value, job)
            weighted_total += weight
            if met:
                weighted_met += weight
            else:
                score -= (weight * 5)  # penalty proportional to weight

        if weighted_total > 0:
            score = max(0, min(100, int(100 - (100 - (weighted_met / weighted_total) * 100))))

        job_with_match = dict(job)
        job_with_match["match_score"] = score
        job_with_match["match_breakdown"] = breakdown
        job_with_match["must_haves_met"] = len(breakdown)
        job_with_match["must_haves_total"] = len(must_haves)
        results.append(job_with_match)

    # Sort by match score (desc), then by posted_date (desc — handle None/string/datetime)
    def _sort_key(j):
        score = j.get("match_score", 0)
        posted = j.get("posted_date") or ""
        # Normalize to a comparable string (ISO dates sort correctly as strings)
        posted_str = posted if isinstance(posted, str) else (posted.isoformat() if hasattr(posted, 'isoformat') else "")
        return (-score, posted_str)
    results.sort(key=_sort_key, reverse=False)
    # reverse=False gives us highest score first (because we negate score)
    # but we want posted_date ascending to break ties by recency — so we actually
    # want score desc, posted_date desc. Let's just do two passes:
    results.sort(key=lambda j: j.get("posted_date") or "", reverse=True)  # recent first
    results.sort(key=lambda j: j.get("match_score", 0), reverse=True)  # then by score (stable)
    return results


def get_priority_dimensions() -> List[Dict]:
    """Return the list of supported priority dimensions for the frontend picker."""
    return [
        {"field": field, **meta}
        for field, meta in PRIORITY_DIMENSIONS.items()
    ]


class JobMatcher:
    """Class wrapper for the matching functions."""

    def match(self, must_haves, priority_weights, jobs):
        return match_jobs(must_haves, priority_weights, jobs)

    def dimensions(self):
        return get_priority_dimensions()


job_matcher = JobMatcher()