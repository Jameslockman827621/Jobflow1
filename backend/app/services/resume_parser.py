"""
Resume Parser Service

Parses uploaded resumes (PDF, DOCX, TXT) and extracts:
- Contact info (name, email, phone, location, LinkedIn, GitHub)
- Skills (curated dictionary + free-text)
- Work experience (title, company, dates, description)
- Education (degree, institution, year)
- Certifications
- Years of experience (computed from dates when available)

Approach:
  1. Normalize text (collapse weird whitespace, normalize dashes).
  2. Find section headers (Experience, Education, Skills, ...).
  3. Parse each section with section-specific logic.

This is intentionally heuristic — it works on the vast majority of
well-structured resumes. For production use, consider pairing it with
an LLM pass (we already do this in cv_tailor when OPENAI_API_KEY is set).
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# Section header patterns (case-insensitive). Order matters — the first match wins.
SECTION_HEADERS = [
    ("experience", re.compile(r"^\s*(?:work\s+)?experience\b", re.IGNORECASE)),
    ("employment", re.compile(r"^\s*employment\s+history\b", re.IGNORECASE)),
    ("education", re.compile(r"^\s*education\b", re.IGNORECASE)),
    ("skills", re.compile(r"^\s*(?:technical\s+)?skills\b", re.IGNORECASE)),
    ("certifications", re.compile(r"^\s*(?:certifications?|licenses?|courses?)\b", re.IGNORECASE)),
    ("projects", re.compile(r"^\s*(?:personal\s+|notable\s+)?projects\b", re.IGNORECASE)),
    ("summary", re.compile(r"^\s*(?:professional\s+summary|summary|profile|about(?:\s+me)?)\b", re.IGNORECASE)),
    ("awards", re.compile(r"^\s*(?:awards?|honors?|achievements?)\b", re.IGNORECASE)),
    ("publications", re.compile(r"^\s*publications?\b", re.IGNORECASE)),
    ("languages", re.compile(r"^\s*languages?\b", re.IGNORECASE)),
    ("interests", re.compile(r"^\s*interests?\b", re.IGNORECASE)),
    ("volunteer", re.compile(r"^\s*volunteer(?:ing)?\b", re.IGNORECASE)),
    ("references", re.compile(r"^\s*references?\b", re.IGNORECASE)),
    ("contact", re.compile(r"^\s*contact(?:\s+information)?\b", re.IGNORECASE)),
]


# A curated skill dictionary — much broader than the original 6 categories.
# Each entry is (canonical_name, regex). The regex matches whole words, case-insensitive.
SKILL_DICTIONARY: List[Tuple[str, str]] = [
    # Languages
    ("Python", r"\bPython\b"),
    ("JavaScript", r"\bJavaScript\b"),
    ("TypeScript", r"\bTypeScript\b"),
    ("Java", r"\bJava\b"),
    ("C++", r"\bC\+\+\b"),
    ("C#", r"\bC#\b"),
    ("Go", r"\bGolang\b|\bGo\b(?=\s*(?:lang|developer|engineer|programmer))"),
    ("Rust", r"\bRust\b"),
    ("Ruby", r"\bRuby\b"),
    ("PHP", r"\bPHP\b"),
    ("Swift", r"\bSwift\b"),
    ("Kotlin", r"\bKotlin\b"),
    ("Scala", r"\bScala\b"),
    ("R", r"\bR\b(?=\s*(?:language|programming|statistical|shiny))"),
    ("SQL", r"\bSQL\b"),
    ("NoSQL", r"\bNoSQL\b"),
    ("HTML", r"\bHTML5?\b"),
    ("CSS", r"\bCSS3?\b"),
    ("SCSS", r"\bSCSS\b"),
    ("Sass", r"\bSass\b"),
    ("Less", r"\bLess\b(?=\s*(?:css|stylesheet|preprocessor))"),
    # Frontend
    ("React", r"\bReact(?:\.js|\.jsx|JS|\.native)?\b"),
    ("React Native", r"\bReact\s+Native\b"),
    ("Next.js", r"\bNext(?:\.js|JS)?\b"),
    ("Vue", r"\bVue(?:\.js|JS)?\b"),
    ("Nuxt", r"\bNuxt(?:\.js|JS)?\b"),
    ("Angular", r"\bAngular(?:JS|\.js)?\b"),
    ("Svelte", r"\bSvelte(?:Kit)?\b"),
    ("Tailwind CSS", r"\bTailwind(?:\s+CSS)?\b"),
    ("Bootstrap", r"\bBootstrap\b"),
    ("Material UI", r"\bMaterial(?:[-\s]?UI)\b"),
    ("Chakra UI", r"\bChakra\b"),
    # Backend
    ("Node.js", r"\bNode(?:\.js|JS)?\b"),
    ("Express", r"\bExpress(?:\.js|JS)?\b"),
    ("NestJS", r"\bNestJS\b|\bNest\.js\b"),
    ("Django", r"\bDjango\b"),
    ("Flask", r"\bFlask\b"),
    ("FastAPI", r"\bFastAPI\b|\bFast[-\s]?API\b"),
    ("Spring", r"\bSpring(?:\s+Boot)?\b"),
    ("Spring Boot", r"\bSpring\s+Boot\b"),
    ("Laravel", r"\bLaravel\b"),
    ("Rails", r"\bRuby\s+on\s+Rails\b|\bRails\b"),
    ("ASP.NET", r"\bASP\.NET\b|\bASP\.NET\s+Core\b"),
    (".NET", r"\b\.NET\b"),
    ("GraphQL", r"\bGraphQL\b"),
    ("gRPC", r"\bgRPC\b"),
    ("REST", r"\bREST(?:ful)?\b"),
    ("WebSockets", r"\bWebSocket[s]?\b"),
    # Databases
    ("PostgreSQL", r"\bPostgreSQL\b|\bPostgres\b"),
    ("MySQL", r"\bMySQL\b"),
    ("MongoDB", r"\bMongoDB\b"),
    ("Redis", r"\bRedis\b"),
    ("Elasticsearch", r"\bElasticsearch\b|\bElastic\s+Search\b"),
    ("DynamoDB", r"\bDynamoDB\b"),
    ("Cassandra", r"\bCassandra\b"),
    ("SQLite", r"\bSQLite\b"),
    ("Oracle", r"\bOracle\b(?=\s*(?:DB|database|SQL))"),
    ("Snowflake", r"\bSnowflake\b"),
    ("BigQuery", r"\bBigQuery\b"),
    ("Dgraph", r"\bDgraph\b"),
    # DevOps / Cloud
    ("Docker", r"\bDocker\b"),
    ("Kubernetes", r"\bKubernetes\b|\bk8s\b"),
    ("AWS", r"\bAWS\b|\bAmazon\s+Web\s+Services\b"),
    ("GCP", r"\bGCP\b|\bGoogle\s+Cloud\b"),
    ("Azure", r"\bAzure\b|\bMicrosoft\s+Azure\b"),
    ("Terraform", r"\bTerraform\b"),
    ("Ansible", r"\bAnsible\b"),
    ("Jenkins", r"\bJenkins\b"),
    ("GitHub Actions", r"\bGitHub\s+Actions\b"),
    ("GitLab CI", r"\bGitLab\s+CI\b"),
    ("CircleCI", r"\bCircleCI\b"),
    ("CI/CD", r"\bCI/?CD\b"),
    ("Pulumi", r"\bPulumi\b"),
    ("CloudFormation", r"\bCloudFormation\b"),
    ("Vagrant", r"\bVagrant\b"),
    ("Helm", r"\bHelm\b"),
    ("Istio", r"\bIstio\b"),
    # Data / ML
    ("Machine Learning", r"\bMachine\s+Learning\b|\bML\b"),
    ("Deep Learning", r"\bDeep\s+Learning\b"),
    ("AI", r"\bAI\b|\bArtificial\s+Intelligence\b"),
    ("TensorFlow", r"\bTensorFlow\b"),
    ("PyTorch", r"\bPyTorch\b"),
    ("Pandas", r"\bPandas\b"),
    ("NumPy", r"\bNumPy\b"),
    ("SciPy", r"\bSciPy\b"),
    ("scikit-learn", r"\bscikit[-\s]?learn\b|\bsklearn\b"),
    ("Spark", r"\bSpark\b|\bApache\s+Spark\b"),
    ("Hadoop", r"\bHadoop\b"),
    ("Kafka", r"\bKafka\b|\bApache\s+Kafka\b"),
    ("Airflow", r"\bAirflow\b|\bApache\s+Airflow\b"),
    ("ETL", r"\bETL\b"),
    ("Data Science", r"\bData\s+Science\b"),
    ("NLP", r"\bNLP\b|\bNatural\s+Language\s+Processing\b"),
    ("Computer Vision", r"\bComputer\s+Vision\b"),
    ("LLM", r"\bLLMs?\b|\bLarge\s+Language\s+Models?\b"),
    # Tools
    ("Git", r"\bGit\b(?!\s*Hub)"),
    ("GitHub", r"\bGitHub\b"),
    ("GitLab", r"\bGitLab\b"),
    ("Bitbucket", r"\bBitbucket\b"),
    ("Jira", r"\bJira\b|\bJIRA\b"),
    ("Confluence", r"\bConfluence\b"),
    ("Slack", r"\bSlack\b"),
    ("Linux", r"\bLinux\b"),
    ("Bash", r"\bBash\b|\bShell\s+Scripting\b"),
    ("PowerShell", r"\bPowerShell\b"),
    ("Agile", r"\bAgile\b"),
    ("Scrum", r"\bScrum\b"),
    ("Kanban", r"\bKanban\b"),
    ("TDD", r"\bTDD\b|\bTest[-\s]?Driven\s+Development\b"),
    # Mobile
    ("iOS", r"\biOS\b"),
    ("Android", r"\bAndroid\b"),
    ("Flutter", r"\bFlutter\b"),
    ("Xamarin", r"\bXamarin\b"),
    # Testing
    ("Jest", r"\bJest\b"),
    ("pytest", r"\bpytest\b"),
    ("Cypress", r"\bCypress\b"),
    ("Selenium", r"\bSelenium\b"),
    ("Playwright", r"\bPlaywright\b"),
    ("JUnit", r"\bJUnit\b"),
    ("Mocha", r"\bMocha\b"),
    # Messaging / Queues
    ("RabbitMQ", r"\bRabbitMQ\b"),
    ("Celery", r"\bCelery\b"),
    ("Sidekiq", r"\bSidekiq\b"),
    ("NATS", r"\bNATS\b"),
    # Concepts
    ("Microservices", r"\bMicroservices?\b"),
    ("REST API", r"\bREST\s+API\b"),
    ("Object-Oriented Programming", r"\bOOP\b|\bObject[-\s]Oriented\s+Programming\b"),
    ("Functional Programming", r"\bFunctional\s+Programming\b"),
]


# Common degree patterns for education extraction
DEGREE_PATTERNS = [
    (r"\b(Ph\.?D\.?|Doctorate(?:\s+of\s+(?:Philosophy|Science|Engineering))?)\b", "PhD"),
    (r"\b(Master\s*of\s+(?:Science|Engineering|Arts|Business\s+Administration)|M\.?S\.?|M\.?A\.?|MBA|M\.?Eng\.?|M\.?Sc\.?)\b", "Master's"),
    (r"\b(Bachelor\s*of\s+(?:Science|Engineering|Arts)|B\.?S\.?|B\.?A\.?|B\.?Eng\.?|B\.?Sc\.?)\b", "Bachelor's"),
    (r"\b(Associate\s+of\s+(?:Science|Arts)|A\.?S\.?|A\.?A\.?)\b", "Associate"),
]


class ResumeParser:
    """Parse resumes and extract structured data."""

    def parse(self, resume_text: str) -> Dict:
        """Parse resume text and extract structured data."""
        if not resume_text:
            return {"contact": {}, "skills": [], "experience": [], "education": [],
                    "certifications": [], "years_of_experience": 0.0}

        text = self._normalize(resume_text)
        sections = self._split_into_sections(text)

        contact = self._extract_contact(text, sections)
        skills = self._extract_skills(text, sections)
        experience = self._extract_experience(text, sections)
        education = self._extract_education(text, sections)
        certs = self._extract_certifications(text, sections)
        years = self._estimate_experience_years(text, experience)

        return {
            "contact": contact,
            "skills": skills,
            "experience": experience,
            "education": education,
            "certifications": certs,
            "years_of_experience": years,
        }

    # ===== HELPERS =====

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize whitespace and dashes."""
        # Replace non-breaking spaces and weird dashes
        text = text.replace("\u00a0", " ").replace("\u2013", "-").replace("\u2014", "-")
        # Strip carriage returns
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Collapse runs of spaces (but preserve newlines)
        text = re.sub(r"[ \t]+", " ", text)
        # Strip trailing whitespace per line
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        return text.strip()

    @staticmethod
    def _split_into_sections(text: str) -> Dict[str, str]:
        """Split the resume into named sections based on header detection."""
        lines = text.split("\n")
        sections: Dict[str, List[str]] = {}
        current = "header"
        sections[current] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                sections[current].append("")
                continue

            matched = None
            for name, pattern in SECTION_HEADERS:
                if pattern.match(stripped):
                    # The header line itself is a section title — don't include it as content.
                    matched = name
                    break

            if matched:
                current = matched
                sections[current] = []
            else:
                sections[current].append(line)

        return {k: "\n".join(v).strip() for k, v in sections.items() if v}

    # ===== CONTACT =====

    def _extract_contact(self, text: str, sections: Dict[str, str]) -> Dict:
        contact: Dict = {}

        # Email
        m = re.search(r"[\w.+-]+@[\w.-]+\.\w{2,}", text)
        if m:
            contact["email"] = m.group()

        # Phone — supports + international, US/UK formats
        phone_patterns = [
            r"\+\d{1,3}[\s.-]?\(?\d{1,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}",
            r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}",
        ]
        for pat in phone_patterns:
            m = re.search(pat, text)
            if m:
                contact["phone"] = m.group().strip()
                break

        # LinkedIn
        m = re.search(r"linkedin\.com/(?:in|pub)/([\w%-]+)", text, re.IGNORECASE)
        if m:
            contact["linkedin"] = f"linkedin.com/in/{m.group(1).rstrip('/')}"

        # GitHub
        m = re.search(r"github\.com/([\w-]+)", text, re.IGNORECASE)
        if m:
            contact["github"] = f"github.com/{m.group(1).rstrip('/')}"

        # Personal website / portfolio
        m = re.search(r"(?:https?://)?(?!linkedin|github|facebook|twitter|x\.com|instagram)([\w-]+\.(?:com|io|dev|me|app|ai|tech|co|net|org))", text, re.IGNORECASE)
        if m:
            contact["website"] = m.group(1)

        # Name — first non-empty line of the document that isn't an email/phone/url
        # and looks like a person's name (1-4 capitalized words).
        header_lines = sections.get("header", "").split("\n")
        for line in header_lines:
            line = line.strip()
            if not line:
                continue
            if "@" in line or "linkedin" in line.lower() or "github" in line.lower():
                continue
            if re.search(r"\d{3}", line):  # skip phone-like
                continue
            # A name is 1-4 capitalized tokens, optionally with a hyphen or apostrophe
            if re.fullmatch(r"[A-Z][\w'’-]+(?:\s+[A-Z][\w'’-]+){0,3}", line):
                contact["name"] = line
                break

        # Location — look for "City, ST" or "City, Country" patterns. We restrict to
        # lines that contain location-like words to avoid false positives like the name.
        location = self._extract_location(text, sections)
        if location:
            contact["location"] = location

        return contact

    @staticmethod
    def _extract_location(text: str, sections: Dict[str, str]) -> Optional[str]:
        # Prefer lines that look like locations in the header or contact section
        candidates = []
        for section_name in ("header", "contact", "summary"):
            section = sections.get(section_name, "")
            for line in section.split("\n"):
                line = line.strip()
                if not line:
                    continue
                # City, State/Country: "London, UK" or "San Francisco, CA" or "New York, NY"
                m = re.search(r"\b([A-Z][\w\s.-]+?),\s*([A-Z]{2}|[A-Z][\w-]+)\b", line)
                if m:
                    candidates.append(m.group(0))
                # "Remote" alone is also a valid location
                elif re.fullmatch(r"Remote(?:,\s*[A-Z][\w-]+)?", line, re.IGNORECASE):
                    candidates.append(line)
                # "City, Country, Region" e.g. "Toronto, ON, Canada"
                m = re.search(r"\b([A-Z][\w\s.-]+?),\s*([A-Z]{2}),\s*([A-Z][\w-]+)\b", line)
                if m:
                    candidates.append(m.group(0))
        return candidates[0] if candidates else None

    # ===== SKILLS =====

    def _extract_skills(self, text: str, sections: Dict[str, str]) -> List[Dict]:
        """Extract skills from the resume."""
        # First, use the curated dictionary on the full text
        skills: List[Dict] = []
        seen = set()
        for canonical, pattern in SKILL_DICTIONARY:
            if re.search(pattern, text, re.IGNORECASE):
                key = canonical.lower()
                if key not in seen:
                    seen.add(key)
                    skills.append({"name": canonical, "category": self._skill_category(canonical)})

        # Then, if there's a dedicated Skills section, also pull free-text tokens
        skills_section = sections.get("skills", "")
        if skills_section:
            # Skills sections often look like "Python, React, AWS" or bullet lists
            for line in skills_section.split("\n"):
                # Strip category prefixes like "Languages: Python, Java"
                line = re.sub(r"^[A-Za-z\s]+:\s*", "", line)
                for token in re.split(r"[,;•·|/]| - ", line):
                    token = token.strip().strip("*-").strip()
                    if not token or len(token) < 2 or len(token) > 40:
                        continue
                    if token.lower() in seen:
                        continue
                    # Skip sentences (skills sections don't have full sentences)
                    if token.count(" ") > 3:
                        continue
                    seen.add(token.lower())
                    skills.append({"name": token, "category": "Other"})

        return skills

    @staticmethod
    def _skill_category(name: str) -> str:
        """Categorize a skill name for downstream filtering."""
        n = name.lower()
        if any(k in n for k in ("react", "vue", "angular", "svelte", "next", "nuxt", "tailwind", "css", "html", "scss", "sass", "bootstrap", "material", "chakra")):
            return "Frontend"
        if any(k in n for k in ("node", "express", "django", "flask", "fastapi", "spring", "laravel", "rails", "asp.net", ".net", "graphql", "grpc", "rest", "websocket")):
            return "Backend"
        if any(k in n for k in ("docker", "kubernetes", "aws", "gcp", "azure", "terraform", "ansible", "jenkins", "ci/cd", "helm", "istio", "pulumi", "cloudformation", "vagrant")):
            return "DevOps"
        if any(k in n for k in ("postgres", "mysql", "mongo", "redis", "elastic", "dynamo", "cassandra", "sqlite", "oracle", "snowflake", "bigquery", "sql", "nosql")):
            return "Database"
        if any(k in n for k in ("machine learning", "deep learning", "ai", "tensorflow", "pytorch", "pandas", "numpy", "scipy", "scikit", "spark", "hadoop", "kafka", "airflow", "etl", "data science", "nlp", "computer vision", "llm")):
            return "Data/ML"
        if any(k in n for k in ("git", "github", "gitlab", "bitbucket", "jira", "confluence", "slack", "linux", "bash", "powershell", "agile", "scrum", "kanban", "tdd")):
            return "Tools"
        if any(k in n for k in ("java", "javascript", "typescript", "python", "c++", "c#", "go", "rust", "ruby", "php", "swift", "kotlin", "scala", " r ")):
            return "Programming"
        return "Other"

    # ===== EXPERIENCE =====

    def _extract_experience(self, text: str, sections: Dict[str, str]) -> List[Dict]:
        """Parse the Experience section into structured entries.

        Recognized line patterns per entry:
          Title at Company  |  Start - End
          Title at Company  |  Start - End  |  Location
          Title, Company  —  Start - End
          Title  —  Company  —  Start - End

        Bullet descriptions follow as lines starting with -, •, or *.
        """
        section = sections.get("experience") or sections.get("employment") or ""
        if not section:
            return []

        experiences: List[Dict] = []
        lines = section.split("\n")
        current: Optional[Dict] = None
        description_lines: List[str] = []

        # Date range pattern — accepts "Jan 2020 - Present", "2020 - 2022",
        # "01/2020 - 12/2022", "2020-Present"
        date_re = re.compile(
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{1,2}/\d{4}|\d{4})"
            r"\s*(?:-|–|—|to)\s*"
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{1,2}/\d{4}|\d{4}|Present|Current|Now|present)",
            re.IGNORECASE,
        )

        def _flush():
            nonlocal current, description_lines
            if current:
                if description_lines:
                    current["description"] = "\n".join(description_lines).strip()
                experiences.append(current)
            current = None
            description_lines = []

        for raw_line in lines:
            line = raw_line.rstrip()
            if not line.strip():
                continue

            stripped = line.strip()

            # A line containing a date range is the header for a new experience entry
            date_match = date_re.search(stripped)
            if date_match:
                _flush()
                start_date, end_date = date_match.group(1), date_match.group(2)
                # The part of the line before the date is "Title at Company" or "Title, Company"
                header = stripped[:date_match.start()].rstrip(" |—–-")
                # Try splitting on " at ", "," or " — "
                title = header
                company = ""
                location = ""
                for sep in (" at ", " - ", " — ", " – ", " | "):
                    if sep in header:
                        parts = header.split(sep, 1)
                        title = parts[0].strip()
                        company = parts[1].strip()
                        break
                if not company and "," in header:
                    parts = header.split(",", 1)
                    title = parts[0].strip()
                    company = parts[1].strip()
                # Strip a trailing location from company if it's "Company, City, ST"
                if company and re.search(r",\s*([A-Z]{2}|[A-Z][\w-]+)$", company):
                    m = re.search(r",\s*([A-Z]{2}|[A-Z][\w-]+)$", company)
                    location = m.group(0).lstrip(", ").strip()
                    company = company[:m.start()].rstrip(", ").strip()

                current = {
                    "title": title,
                    "company": company,
                    "start_date": start_date,
                    "end_date": end_date,
                    "location": location,
                    "description": "",
                }
                continue

            # Bullet lines belong to the current entry's description
            if re.match(r"^\s*[-•*▪◦●○]\s+", stripped) or re.match(r"^\s*\d+[.)]\s+", stripped):
                # Strip the bullet marker
                bullet = re.sub(r"^\s*[-•*▪◦●○]\s+", "", stripped)
                bullet = re.sub(r"^\s*\d+[.)]\s+", "", bullet)
                if current:
                    description_lines.append(bullet)
                continue

            # If we don't have a current entry yet, treat any non-empty line as a potential header
            # for the next entry (e.g., a bare title line followed by a date line).
            if current is None:
                # Heuristic: a short line that isn't a sentence is likely a job title
                if len(stripped) < 80 and stripped.count(" ") <= 6 and not stripped.endswith("."):
                    current = {
                        "title": stripped,
                        "company": "",
                        "start_date": "",
                        "end_date": "",
                        "location": "",
                        "description": "",
                    }
                continue

            # If current exists and the line isn't a bullet, treat it as a description sentence
            description_lines.append(stripped)

        _flush()
        return experiences

    # ===== EDUCATION =====

    def _extract_education(self, text: str, sections: Dict[str, str]) -> List[Dict]:
        section = sections.get("education", "")
        education: List[Dict] = []

        # If we have a dedicated education section, parse line by line
        if section:
            for line in section.split("\n"):
                line = line.strip()
                if not line:
                    continue
                degree = self._match_degree(line)
                if degree:
                    # Try to find a year
                    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", line)
                    # Try to find an institution (text after the degree that isn't a year)
                    institution = ""
                    # Strip the degree match
                    after = re.sub(r"\b(Ph\.?D\.?|Doctorate(?:\s+of\s+\w+)?|Master(?:'s|\sof\s+\w+)?|M\.?S\.?|M\.?A\.?|MBA|M\.?Eng\.?|M\.?Sc\.?|Bachelor(?:'s|\sof\s+\w+)?|B\.?S\.?|B\.?A\.?|B\.?Eng\.?|B\.?Sc\.?|Associate(?:\s+of\s+\w+)?)\b", "", line, flags=re.IGNORECASE)
                    after = re.sub(r"\b(19\d{2}|20\d{2})\b", "", after)
                    after = re.sub(r"[,|·•]+", " ", after).strip(" -|—")
                    if after and len(after) < 100:
                        institution = after.strip()
                    education.append({
                        "degree": degree,
                        "field": "",
                        "institution": institution,
                        "graduation_year": year_match.group(1) if year_match else "",
                    })

        # Fallback: scan the whole text for degree mentions
        if not education:
            for pattern, label in DEGREE_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", text)
                    education.append({
                        "degree": label,
                        "field": "",
                        "institution": "",
                        "graduation_year": year_match.group(1) if year_match else "",
                    })
                    break

        return education

    @staticmethod
    def _match_degree(line: str) -> str:
        for pattern, label in DEGREE_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                return label
        return ""

    # ===== CERTIFICATIONS =====

    def _extract_certifications(self, text: str, sections: Dict[str, str]) -> List[Dict]:
        section = sections.get("certifications", "")
        certs: List[Dict] = []
        seen = set()

        # Pattern-based scan on the section (or full text as fallback)
        cert_patterns = [
            r"\b(AWS Certified [\w\s-]+?)\b(?=\s*[-,•·|]|$)",
            r"\b(Google Cloud Certified [\w\s-]+?)\b(?=\s*[-,•·|]|$)",
            r"\b(Microsoft Certified[:\s][\w\s-]+?)\b(?=\s*[-,•·|]|$)",
            r"\b(Certified [\w\s]+ Professional)\b",
            r"\b(PMP|CAPM|CISSP|CEH|CCSP|CCNA|CCNP|CKA|CKAD|AWS Solutions? Architect)\b",
        ]
        source = section if section else text
        for pattern in cert_patterns:
            for m in re.finditer(pattern, source, re.IGNORECASE):
                name = m.group(0).strip()
                key = name.lower()
                if key not in seen:
                    seen.add(key)
                    certs.append({"name": name, "issuer": "", "year": ""})

        return certs

    # ===== EXPERIENCE YEARS =====

    def _estimate_experience_years(self, text: str, experiences: List[Dict]) -> float:
        """Estimate total years of experience."""
        # 1. Explicit mention in summary ("5+ years of experience")
        m = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?|y\.?)\s+(?:of\s+)?(?:experience|exp\.?)", text, re.IGNORECASE)
        if m:
            return float(m.group(1))

        # 2. Sum from parsed experience date ranges
        total_months = 0
        for exp in experiences:
            start = self._parse_date(exp.get("start_date", ""))
            end = self._parse_date(exp.get("end_date", ""))
            if not end:
                end = datetime.utcnow()
            if start and end and end > start:
                months = (end.year - start.year) * 12 + (end.month - start.month)
                if months > 0:
                    total_months += months
        if total_months > 0:
            return round(total_months / 12, 1)

        # 3. Fallback: count entries * 2.5
        if experiences:
            return round(len(experiences) * 2.5, 1)

        return 0.0

    @staticmethod
    def _parse_date(value: str) -> Optional[datetime]:
        if not value:
            return None
        s = str(value).strip().rstrip(".")
        # "Present", "Current", "Now"
        if s.lower() in ("present", "current", "now"):
            return datetime.utcnow()
        # "Jan 2020", "January 2020"
        for fmt in ("%b %Y", "%B %Y", "%m/%Y", "%Y", "%Y-%m", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None


# Singleton
resume_parser = ResumeParser()
