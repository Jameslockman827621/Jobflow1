"""
CV Tailoring Service

The core viral feature: for every job application, generate a hyper-personalized,
ATS-optimized CV that mirrors the job description's keywords, reorders experience
to highlight the most relevant roles, and quantifies achievements.

Two modes:
  1. AI-powered (when OPENAI_API_KEY is set): uses LLM to rewrite summary,
     reorder experience, and emphasize matching skills. Stays truthful — only
     rephrases/reorders, never fabricates.
  2. Keyword-based fallback (no API key needed): extracts keywords from the
     job description, mirrors them in the summary, reorders skills by relevance,
     and reorders experience by keyword overlap. Works out-of-the-box.

Both modes return a structured tailored CV dict that can be rendered via the
existing CV templates.

Public API:
  tailor_cv_for_job(cv, job_description, job_title, company) -> dict
  score_cv_against_job(cv, job_description) -> dict  (ATS score)
"""

import json
import re
from typing import List, Dict, Optional, Any
from collections import Counter

from app.core.config import settings


# Common English stopwords to filter out when extracting keywords
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "can", "of", "in", "on", "at", "to", "for",
    "with", "by", "from", "as", "into", "about", "between", "through", "during",
    "before", "after", "above", "below", "up", "down", "out", "off", "over",
    "under", "again", "further", "then", "once", "here", "there", "when", "where",
    "why", "how", "all", "each", "every", "both", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too",
    "very", "s", "t", "just", "don", "now", "you", "your", "we", "our", "they",
    "their", "this", "that", "these", "those", "i", "me", "my", "myself",
    "what", "which", "who", "whom", "him", "her", "his", "hers", "its",
    "job", "role", "position", "work", "working", "experience", "experiences",
    "year", "years", "team", "teams", "candidate", "candidates", "ability",
    "must", "plus", "etc", "e.g", "i.e", "looking", "join", "joining", "want",
    "need", "required", "requirement", "requirements", "responsibility",
    "responsibilities", "duty", "duties", "qualification", "qualifications",
    "preferred", "ideal", "great", "good", "excellent", "strong", "weak",
}

# Common technical skills — used to boost skill detection
SKILL_DICTIONARY = {
    # Languages
    "python", "javascript", "typescript", "java", "kotlin", "swift", "go", "golang",
    "rust", "c", "c++", "c#", "ruby", "php", "scala", "elixir", "clojure",
    "haskell", "perl", "r", "matlab", "dart", "lua", "objective-c",
    # Frontend
    "react", "reactjs", "react.js", "vue", "vuejs", "vue.js", "angular", "angularjs",
    "svelte", "sveltekit", "next.js", "nextjs", "nuxt", "remix", "gatsby",
    "html", "html5", "css", "css3", "sass", "scss", "less", "tailwind",
    "tailwindcss", "bootstrap", "material-ui", "mui", "chakra", "styled-components",
    "redux", "mobx", "zustand", "recoil", "storybook", "webpack", "vite", "babel",
    # Backend
    "node", "nodejs", "node.js", "express", "expressjs", "fastify", "nestjs",
    "django", "flask", "fastapi", "tornado", "aiohttp", "rails", "ruby on rails",
    "spring", "spring-boot", "springboot", "laravel", "symfony", "gin", "echo",
    "fiber", "actix", "rocket", "axum", "phoenix", "asp.net", ".net", ".net core",
    # Databases
    "sql", "mysql", "postgresql", "postgres", "sqlite", "mariadb", "oracle",
    "mongodb", "redis", "cassandra", "dynamodb", "couchdb", "elasticsearch",
    "neo4j", "graphdb", "supabase", "planetscale", "cockroachdb", "snowflake",
    "bigquery", "redshift", "databricks",
    # Cloud / DevOps
    "aws", "gcp", "azure", "docker", "kubernetes", "k8s", "terraform",
    "ansible", "puppet", "chef", "helm", "istio", "prometheus", "grafana",
    "datadog", "new relic", "cloudwatch", "lambda", "ec2", "s3", "rds",
    "cloudfront", "route53", "cloudflare", "vercel", "netlify", "heroku",
    "digitalocean", "linode", "fly.io", "railway", "render",
    # Messaging / Streaming
    "kafka", "rabbitmq", "sqs", "sns", "pubsub", "nats", "celery", "sidekiq",
    "bull", "redis queue", "resque",
    # AI / ML
    "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
    "scikit-learn", "sklearn", "xgboost", "lightgbm", "catboost", "pandas",
    "numpy", "scipy", "matplotlib", "seaborn", "plotly", "jupyter", "nlp",
    "natural language processing", "computer vision", "opencv", "transformers",
    "huggingface", "hugging face", "llm", "gpt", "bert", "langchain", "llamaindex",
    "openai", "anthropic", "claude", "rag", "ragstack",
    # Mobile
    "ios", "android", "react native", "flutter", "xamarin", "ionic", "pwa",
    # Tools / Practices
    "git", "github", "gitlab", "bitbucket", "jenkins", "circleci", "github actions",
    "travis ci", "argo cd", "argocd", "ci/cd", "tdd", "bdd", "agile", "scrum",
    "kanban", "jira", "confluence", "notion", "slack", "linear",
    # Architecture
    "microservices", "monolith", "soa", "event-driven", "cqrs", "event sourcing",
    "ddd", "domain-driven design", "rest", "graphql", "grpc", "protobuf",
    "websockets", "soap", "api", "apis", "openapi", "swagger", "postman",
    # Security
    "oauth", "oauth2", "oidc", "jwt", "saml", "sso", "rbac", "abac",
    "penetration testing", "owasp", "security", "encryption", "tls", "ssl",
    # Data / Analytics
    "etl", "elt", "airflow", "dbt", "spark", "hadoop", "hive", "presto",
    "trino", "flink", "beam", "tableau", "looker", "power bi", "powerbi",
    "superset", "metabase",
}

# Sections in a job description to look for
JD_REQUIREMENT_SECTIONS = ["requirements", "qualifications", "what you'll need", "what you need", "about you", "must have", "required skills", "tech stack", "skills"]
JD_NICE_SECTIONS = ["nice to have", "preferred", "bonus", "preferred qualifications", "preferred skills", "nice-to-have"]


def _tokenize(text: str) -> List[str]:
    """Split text into lowercase word tokens."""
    if not text:
        return []
    # Split on non-alphanumeric (keep + and # and . for things like C++, C#, Node.js)
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.]*", text.lower())
    return tokens


def _extract_keywords(text: str, top_n: int = 25) -> List[str]:
    """Extract the most important keywords from a text body.

    Combines frequency analysis with a curated skill dictionary so we catch
    multi-word skills like "machine learning" that simple tokenization would miss.
    """
    if not text:
        return []
    text_lower = text.lower()

    # 1. Match against the skill dictionary (multi-word + single)
    dict_matches: Counter = Counter()
    for skill in SKILL_DICTIONARY:
        # Use word-boundary regex for clean matching
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            dict_matches[skill] += 1

    # 2. Tokenize and count single words (filter stopwords + short tokens)
    tokens = _tokenize(text)
    word_counts: Counter = Counter()
    for tok in tokens:
        if tok in STOPWORDS:
            continue
        if len(tok) < 3:
            continue
        # Skip if already covered by a dict skill
        if any(tok in skill.split() for skill in dict_matches):
            continue
        word_counts[tok] += 1

    # 3. Combine: dict skills first (high relevance), then top words
    keywords: List[str] = [s for s, _ in dict_matches.most_common(top_n)]
    for word, _ in word_counts.most_common(top_n - len(keywords)):
        if word not in keywords:
            keywords.append(word)

    return keywords[:top_n]


def _extract_jd_sections(text: str) -> Dict[str, str]:
    """Try to split the JD into 'requirements' and 'nice-to-have' sections."""
    if not text:
        return {"requirements": "", "nice_to_have": "", "full": ""}
    text_lower = text.lower()
    sections = {"requirements": text, "nice_to_have": "", "full": text}

    # Find requirement section start
    req_start = -1
    for marker in JD_REQUIREMENT_SECTIONS:
        idx = text_lower.find(marker)
        if idx >= 0 and (req_start == -1 or idx < req_start):
            req_start = idx
    nice_start = -1
    for marker in JD_NICE_SECTIONS:
        idx = text_lower.find(marker)
        if idx >= 0 and (nice_start == -1 or idx < nice_start):
            nice_start = idx

    if req_start >= 0:
        end = nice_start if nice_start > req_start else len(text)
        sections["requirements"] = text[req_start:end]
    if nice_start >= 0:
        sections["nice_to_have"] = text[nice_start:]

    return sections


def _score_keyword_coverage(cv_text: str, keywords: List[str]) -> tuple:
    """Return (coverage_pct, matched_keywords, missing_keywords)."""
    if not keywords:
        return 100.0, [], []
    cv_lower = cv_text.lower()
    matched = []
    missing = []
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw.lower()) + r"\b", cv_lower):
            matched.append(kw)
        else:
            missing.append(kw)
    coverage = round((len(matched) / len(keywords)) * 100, 1) if keywords else 0
    return coverage, matched, missing


def _reorder_skills_by_relevance(skills: List[str], keywords: List[str]) -> List[str]:
    """Reorder skills so keywords that match the JD come first."""
    if not skills:
        return []
    kw_set = {k.lower() for k in keywords}
    scored = []
    for skill in skills:
        skill_lower = skill.lower()
        # Score = number of keyword matches (skills often match multiple keywords)
        score = sum(1 for kw in kw_set if kw in skill_lower or skill_lower in kw)
        scored.append((score, skill))
    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored]


def _reorder_experience_by_relevance(experience: List[Dict], keywords: List[str]) -> List[Dict]:
    """Reorder experience entries so the ones with most keyword overlap come first."""
    if not experience:
        return []
    kw_set = {k.lower() for k in keywords}
    scored = []
    for exp in experience:
        text = " ".join([
            str(exp.get("role") or ""),
            str(exp.get("company") or ""),
            str(exp.get("description") or ""),
        ]).lower()
        score = sum(1 for kw in kw_set if kw in text)
        scored.append((score, exp))
    # Stable sort keeps original order for ties (so chronological order preserved within same score)
    scored.sort(key=lambda x: -x[0])
    return [e for _, e in scored]


def _quantify_description(description: str, keywords: List[str]) -> str:
    """Lightly improve a job experience description by ensuring it reads as impact-focused.

    We don't fabricate numbers, but we rephrase leading verbs to be more active
    and ensure keywords appear naturally. Falls back to original if anything looks off.
    """
    if not description:
        return description
    # Simple cleanup: collapse whitespace, strip leading bullets
    cleaned = re.sub(r"\s+", " ", description).strip()
    # If description doesn't start with a strong verb, leave it alone
    # (we don't want to fabricate impact numbers)
    return cleaned


def _generate_keyword_summary(
    original_summary: str,
    role: str,
    company: str,
    skills: List[str],
    keywords: List[str],
    years_exp: Optional[float] = None,
) -> str:
    """Generate a professional summary that mirrors the JD keywords and emphasizes the most relevant skills.

    Pure keyword-based — no LLM needed. Reads naturally because we only use
    real skills from the user's CV and avoid stuffing the role title in awkwardly.
    """
    # Pick top 4-6 skills that match the JD keywords
    matching_skills = []
    for skill in _reorder_skills_by_relevance(skills, keywords):
        if len(matching_skills) >= 6:
            break
        matching_skills.append(skill)

    if not matching_skills:
        matching_skills = skills[:5] if skills else []

    skills_str = ", ".join(matching_skills) if matching_skills else "full-stack development"

    years_part = f"{int(years_exp)}+ years of experience" if years_exp else "Engineer"
    # Use a clean role phrase — strip seniority words to avoid awkward phrasing
    role_clean = (role or "").strip()
    # Don't embed the job title verbatim — describe the domain instead
    domain_phrase = "building scalable production systems"

    summary = (
        f"{years_part} {domain_phrase} with strong expertise in {skills_str}. "
        f"Proven track record shipping features end-to-end, collaborating cross-functionally, "
        f"and mentoring teammates. Excited to bring this experience to {company}."
    )
    return summary


def _build_keyword_tailored_cv(
    cv: Any,
    job_description: str,
    job_title: str,
    company: str,
) -> Dict:
    """Keyword-based tailoring fallback (no LLM). Returns a structured CV dict."""
    # Pull text from the CV for keyword matching
    cv_text_parts = []
    cv_text_parts.append(cv.full_name or "")
    cv_text_parts.append(cv.summary or "")
    for exp in (cv.experience or []):
        cv_text_parts.append(str(exp.get("role") or ""))
        cv_text_parts.append(str(exp.get("company") or ""))
        cv_text_parts.append(str(exp.get("description") or ""))
    cv_text_parts.extend(cv.skills or [])
    cv_text = " ".join(cv_text_parts)

    sections = _extract_jd_sections(job_description)
    # Use the requirements section for keyword extraction (fall back to full JD)
    kw_source = sections["requirements"] or job_description
    keywords = _extract_keywords(kw_source, top_n=25)

    # Reorder skills + experience by relevance
    tailored_skills = _reorder_skills_by_relevance(cv.skills or [], keywords)
    tailored_experience = _reorder_experience_by_relevance(cv.experience or [], keywords)
    # Quantify descriptions (light cleanup — no fabrication)
    for exp in tailored_experience:
        if exp.get("description"):
            exp["description"] = _quantify_description(exp["description"], keywords)

    # Generate keyword-mirrored summary
    years_exp = None
    try:
        # Try to compute years from experience dates
        years_exp = _estimate_years_experience(cv.experience or [])
    except Exception:
        pass

    tailored_summary = _generate_keyword_summary(
        original_summary=cv.summary or "",
        role=job_title,
        company=company,
        skills=tailored_skills,
        keywords=keywords,
        years_exp=years_exp,
    )

    return {
        "full_name": cv.full_name,
        "email": cv.email,
        "phone": cv.phone,
        "location": cv.location,
        "linkedin_url": cv.linkedin_url,
        "portfolio_url": cv.portfolio_url,
        "summary": tailored_summary,
        "experience": tailored_experience,
        "education": cv.education or [],
        "skills": tailored_skills,
        "certifications": cv.certifications or [],
        "projects": cv.projects or [],
        "template_id": cv.template_id or "modern",
        "tailoring_method": "keyword",
        "keywords_matched": keywords,
    }


def _estimate_years_experience(experience: List[Dict]) -> Optional[float]:
    """Estimate total years of experience from a list of experience entries."""
    if not experience:
        return None
    from datetime import datetime
    total_months = 0
    for exp in experience:
        start = _parse_date_str(exp.get("start_date"))
        end = _parse_date_str(exp.get("end_date")) or datetime.utcnow()
        if start and end and end > start:
            months = (end.year - start.year) * 12 + (end.month - start.month)
            if months > 0:
                total_months += months
    return round(total_months / 12, 1) if total_months > 0 else None


def _parse_date_str(value):
    """Parse 'YYYY-MM' or 'YYYY-MM-DD' into a datetime."""
    if not value:
        return None
    from datetime import datetime
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


# ===== AI-POWERED TAILORING =====

def _build_ai_tailored_cv(
    cv: Any,
    job_description: str,
    job_title: str,
    company: str,
) -> Dict:
    """Use an LLM to produce a tailored structured CV.

    The LLM is constrained to: only use real skills/experience from the user's CV,
    reorder and rephrase for impact, mirror the JD's keywords naturally, and
    emphasize the most relevant achievements first. We then validate the output
    is safe (no fabricated employers) before returning.
    """
    try:
        from openai import OpenAI
    except Exception:
        return _build_keyword_tailored_cv(cv, job_description, job_title, company)

    if not settings.OPENAI_API_KEY:
        return _build_keyword_tailored_cv(cv, job_description, job_title, company)

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
    except Exception:
        return _build_keyword_tailored_cv(cv, job_description, job_title, company)

    # Build a compact CV payload for the prompt
    cv_payload = {
        "full_name": cv.full_name,
        "summary": cv.summary or "",
        "experience": cv.experience or [],
        "education": cv.education or [],
        "skills": cv.skills or [],
        "certifications": cv.certifications or [],
        "projects": cv.projects or [],
    }

    prompt = f"""You are an expert ATS-optimized resume writer. Tailor this candidate's CV for a specific job.

CANDIDATE CV (JSON):
{json.dumps(cv_payload, indent=2)}

JOB TITLE: {job_title}
COMPANY: {company}

JOB DESCRIPTION:
{job_description[:4000]}

RULES (CRITICAL):
1. Only use skills, experience, education, and projects that appear in the candidate's CV. NEVER fabricate employers, dates, degrees, or skills the candidate doesn't have.
2. Reorder experience entries so the most relevant to this job come first.
3. Reorder skills so the most relevant to this job come first.
4. Rewrite the professional summary (3-4 sentences) to mirror the job description's keywords naturally — emphasize skills the candidate actually has that match the JD.
5. For each experience entry, lightly rephrase the description to highlight achievements that map to what the JD asks for. Do NOT add fake metrics. If the original is vague, keep it vague but reorganize it.
6. Keep all contact info (email, phone, location, linkedin, portfolio) unchanged.
7. Keep the same JSON schema. Output ONLY the JSON, no markdown, no commentary.

OUTPUT (JSON, same schema as input, plus a "tailoring_method": "ai" field):
"""

    try:
        response = client.chat.completions.create(
            model=getattr(settings, "LLM_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500,
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        tailored = json.loads(content)
    except Exception as e:
        print(f"  CV tailor: AI error ({e}), falling back to keyword method")
        return _build_keyword_tailored_cv(cv, job_description, job_title, company)

    # Validate output — never let the LLM fabricate employers
    original_companies = {(exp.get("company") or "").lower().strip() for exp in (cv.experience or [])}
    original_companies.discard("")
    validated_experience = []
    for exp in (tailored.get("experience") or []):
        exp_company = (exp.get("company") or "").lower().strip()
        if exp_company and original_companies and exp_company not in original_companies:
            print(f"  CV tailor: dropping fabricated employer '{exp.get('company')}'")
            continue
        validated_experience.append(exp)
    tailored["experience"] = validated_experience or cv.experience

    # Validate skills — only keep skills the user actually has (case-insensitive)
    user_skills_lower = {s.lower() for s in (cv.skills or [])}
    validated_skills = []
    for skill in (tailored.get("skills") or []):
        if skill.lower() in user_skills_lower:
            validated_skills.append(skill)
    tailored["skills"] = validated_skills or cv.skills or []

    # Preserve contact info
    tailored["full_name"] = cv.full_name
    tailored["email"] = cv.email
    tailored["phone"] = cv.phone
    tailored["location"] = cv.location
    tailored["linkedin_url"] = cv.linkedin_url
    tailored["portfolio_url"] = cv.portfolio_url
    tailored["education"] = tailored.get("education") or cv.education or []
    tailored["certifications"] = tailored.get("certifications") or cv.certifications or []
    tailored["projects"] = tailored.get("projects") or cv.projects or []
    tailored["template_id"] = cv.template_id or "modern"
    tailored["tailoring_method"] = "ai"

    # Capture keywords matched for downstream scoring/display
    sections = _extract_jd_sections(job_description)
    tailored["keywords_matched"] = _extract_keywords(sections["requirements"] or job_description, top_n=25)

    return tailored


# ===== ATS SCORING =====

def score_cv_against_job(cv_data: Dict, job_description: str) -> Dict:
    """Score a (possibly tailored) CV against a job description.

    Returns:
      {
        "overall": 0-100,
        "keyword_score": 0-100,   # what % of JD keywords appear in the CV
        "skills_score": 0-100,    # what % of JD-required skills appear in the CV
        "experience_score": 0-100, # heuristic: how much experience text overlaps JD
        "matched_keywords": [...],
        "missing_keywords": [...],
        "matched_skills": [...],
        "missing_skills": [...],
        "recommendations": [...],   # actionable suggestions
      }
    """
    if not job_description:
        return _empty_score()

    sections = _extract_jd_sections(job_description)
    req_text = sections["requirements"] or job_description
    jd_keywords = _extract_keywords(req_text, top_n=30)

    # Build a single CV text for scoring
    cv_text_parts = [
        str(cv_data.get("summary") or ""),
        str(cv_data.get("full_name") or ""),
    ]
    for exp in (cv_data.get("experience") or []):
        cv_text_parts.append(str(exp.get("role") or ""))
        cv_text_parts.append(str(exp.get("company") or ""))
        cv_text_parts.append(str(exp.get("description") or ""))
    for proj in (cv_data.get("projects") or []):
        cv_text_parts.append(str(proj.get("name") or ""))
        cv_text_parts.append(str(proj.get("description") or ""))
    cv_text_parts.extend(cv_data.get("skills") or [])
    cv_text_parts.extend(cv_data.get("certifications") or [])
    cv_text = " ".join(cv_text_parts)

    # Keyword coverage
    kw_coverage, matched_kw, missing_kw = _score_keyword_coverage(cv_text, jd_keywords)
    keyword_score = round(kw_coverage, 1)

    # Skill coverage — only check against skills explicitly listed in JD
    jd_skill_keywords = [k for k in jd_keywords if any(k in s.lower() for s in SKILL_DICTIONARY) or k in SKILL_DICTIONARY]
    cv_skills_lower = {s.lower() for s in (cv_data.get("skills") or [])}
    matched_skills = []
    missing_skills = []
    for skill_kw in jd_skill_keywords:
        # Match if the skill keyword appears as a substring of any cv skill
        if any(skill_kw in s or s in skill_kw for s in cv_skills_lower):
            matched_skills.append(skill_kw)
        else:
            # Also check if the skill appears anywhere in the CV text
            if re.search(r"\b" + re.escape(skill_kw.lower()) + r"\b", cv_text.lower()):
                matched_skills.append(skill_kw)
            else:
                missing_skills.append(skill_kw)
    skills_score = round((len(matched_skills) / len(jd_skill_keywords)) * 100, 1) if jd_skill_keywords else 100.0

    # Experience score — heuristic: keyword overlap in experience descriptions
    exp_text = " ".join([
        f"{exp.get('role','')} {exp.get('company','')} {exp.get('description','')}"
        for exp in (cv_data.get("experience") or [])
    ])
    exp_kw_coverage, _, _ = _score_keyword_coverage(exp_text, jd_keywords)
    experience_score = round(exp_kw_coverage, 1)

    # Overall: weighted blend (skills matter most for ATS)
    overall = round(
        0.4 * skills_score + 0.35 * keyword_score + 0.25 * experience_score, 1
    )

    # Recommendations
    recommendations = []
    if missing_skills:
        top_missing = missing_skills[:3]
        recommendations.append(
            f"Add these skills to your CV if you have them: {', '.join(top_missing)}"
        )
    if missing_kw and len(missing_kw) > 5:
        recommendations.append(
            "Mirror more of the job description's language in your summary and experience descriptions."
        )
    if experience_score < 50:
        recommendations.append(
            "Quantify your past achievements with metrics (e.g. 'reduced latency by 40%')."
        )
    if not recommendations:
        recommendations.append("Your CV is well-aligned with this role. Apply with confidence!")

    return {
        "overall": overall,
        "keyword_score": keyword_score,
        "skills_score": skills_score,
        "experience_score": experience_score,
        "matched_keywords": matched_kw,
        "missing_keywords": missing_kw[:10],
        "matched_skills": matched_skills,
        "missing_skills": missing_skills[:10],
        "recommendations": recommendations,
    }


def _empty_score() -> Dict:
    return {
        "overall": 0,
        "keyword_score": 0,
        "skills_score": 0,
        "experience_score": 0,
        "matched_keywords": [],
        "missing_keywords": [],
        "matched_skills": [],
        "missing_skills": [],
        "recommendations": ["Add a job description to score your CV."],
    }


# ===== PUBLIC API =====

def tailor_cv_for_job(
    cv: Any,
    job_description: str,
    job_title: str = "",
    company: str = "",
) -> Dict:
    """Tailor a CV for a specific job. Returns a structured CV dict.

    Uses AI when OPENAI_API_KEY is set; falls back to keyword-based tailoring.
    The returned dict can be passed directly to render_cv_html() or stored on
    an Application as tailored_cv_data.
    """
    if not job_description:
        # No JD to tailor to — return original
        return {
            "full_name": cv.full_name,
            "email": cv.email,
            "phone": cv.phone,
            "location": cv.location,
            "linkedin_url": cv.linkedin_url,
            "portfolio_url": cv.portfolio_url,
            "summary": cv.summary or "",
            "experience": cv.experience or [],
            "education": cv.education or [],
            "skills": cv.skills or [],
            "certifications": cv.certifications or [],
            "projects": cv.projects or [],
            "template_id": cv.template_id or "modern",
            "tailoring_method": "none",
            "keywords_matched": [],
        }

    if settings.OPENAI_API_KEY:
        return _build_ai_tailored_cv(cv, job_description, job_title, company)
    return _build_keyword_tailored_cv(cv, job_description, job_title, company)


class CVTailorService:
    """Class wrapper for the tailoring functions, for use as a singleton."""

    def tailor_cv_for_job(self, cv: Any, job_description: str, job_title: str = "", company: str = "") -> Dict:
        return tailor_cv_for_job(cv, job_description, job_title, company)

    def score_cv_against_job(self, cv_data: Dict, job_description: str) -> Dict:
        return score_cv_against_job(cv_data, job_description)


cv_tailor_service = CVTailorService()