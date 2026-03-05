"""
Resume Parser Service

Parses uploaded resumes (PDF, DOCX, TXT) and extracts:
- Contact info
- Skills
- Experience
- Education
- Certifications

Uses regex patterns and NLP for extraction.
For production, consider:
- Affinda API
- Sovren
- RChilli
- Custom ML model
"""

import re
from typing import Dict, List, Optional
from datetime import datetime


class ResumeParser:
    """Parse resumes and extract structured data"""
    
    # Common skill patterns
    SKILL_CATEGORIES = {
        "Programming": [
            r'\b(Python|Java|JavaScript|TypeScript|C\+\+|C#|Go|Rust|Ruby|PHP|Swift|Kotlin|Rust)\b',
            r'\b(SQL|NoSQL|MongoDB|PostgreSQL|MySQL|Redis|Elasticsearch)\b',
        ],
        "Frontend": [
            r'\b(React|Vue|Angular|Svelte|Next\.js|Nuxt|HTML|CSS|SCSS|Tailwind)\b',
        ],
        "Backend": [
            r'\b(Node\.?js|Django|Flask|FastAPI|Spring|Express|Laravel|Rails)\b',
            r'\b(REST|GraphQL|gRPC|Microservices|API)\b',
        ],
        "DevOps": [
            r'\b(Docker|Kubernetes|AWS|GCP|Azure|Terraform|Ansible|Jenkins|CI/CD)\b',
        ],
        "Data": [
            r'\b(Machine Learning|ML|AI|Data Science|TensorFlow|PyTorch|Pandas|NumPy)\b',
            r'\b(Spark|Hadoop|Kafka|Airflow|ETL)\b',
        ],
        "Tools": [
            r'\b(Git|Linux|Bash|Agile|Scrum|JIRA|Confluence)\b',
        ],
    }
    
    # Education patterns
    EDUCATION_PATTERNS = [
        r'(Bachelor[\'s]?|B\.?S\.?|B\.?A\.?)\s+(?:of\s+)?(\w+(?:\s+\w+)?)',
        r'(Master[\'s]?|M\.?S\.?|M\.?A\.?|MBA|M\.?B\.?A\.?)\s+(?:of\s+)?(\w+(?:\s+\w+)?)',
        r'(Ph\.?D\.?|Doctorate)\s+(?:of\s+)?(\w+(?:\s+\w+)?)',
    ]
    
    def parse(self, resume_text: str) -> Dict:
        """Parse resume text and extract structured data"""
        return {
            "contact": self._extract_contact(resume_text),
            "skills": self._extract_skills(resume_text),
            "experience": self._extract_experience(resume_text),
            "education": self._extract_education(resume_text),
            "certifications": self._extract_certifications(resume_text),
            "years_of_experience": self._estimate_experience_years(resume_text),
        }
    
    def _extract_contact(self, text: str) -> Dict:
        """Extract contact information"""
        contact = {}
        
        # Email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            contact['email'] = email_match.group()
        
        # Phone (various formats)
        phone_patterns = [
            r'\+?1?\s*\(?[0-9]{3}\)?[\s\.-]?[0-9]{3}[\s\.-]?[0-9]{4}',
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                contact['phone'] = phone_match.group()
                break
        
        # LinkedIn
        linkedin_match = re.search(r'linkedin\.com/in/([\w-]+)', text, re.IGNORECASE)
        if linkedin_match:
            contact['linkedin'] = f"linkedin.com/in/{linkedin_match.group(1)}"
        
        # GitHub
        github_match = re.search(r'github\.com/([\w-]+)', text, re.IGNORECASE)
        if github_match:
            contact['github'] = f"github.com/{github_match.group(1)}"
        
        # Location (city, state/country)
        location_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?\s*([A-Z]{2}|[A-Z][a-z]+)', text)
        if location_match:
            contact['location'] = f"{location_match.group(1)}, {location_match.group(2)}"
        
        return contact
    
    def _extract_skills(self, text: str) -> List[Dict]:
        """Extract skills from resume"""
        skills = []
        seen = set()
        
        for category, patterns in self.SKILL_CATEGORIES.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    skill_name = match if isinstance(match, str) else match[0]
                    if skill_name.lower() not in seen:
                        seen.add(skill_name.lower())
                        skills.append({
                            "name": skill_name,
                            "category": category,
                        })
        
        return skills
    
    def _extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience"""
        experiences = []
        
        # Look for job-like patterns
        # This is simplified - production would use ML
        job_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*\n?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*\n?\s*(\d{4}|\w+\s+\d{4})\s*[-–]\s*(\d{4}|Present|Current)'
        
        matches = re.findall(job_pattern, text)
        for match in matches[:5]:  # Limit to 5 most recent
            experiences.append({
                "title": match[0],
                "company": match[1],
                "start_date": match[2],
                "end_date": match[3],
            })
        
        return experiences
    
    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education"""
        education = []
        
        for pattern in self.EDUCATION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                education.append({
                    "degree": match[0],
                    "field": match[1] if len(match) > 1 else "",
                })
        
        return education
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        certs = []
        
        # Common certification patterns
        cert_patterns = [
            r'\b(AWS Certified\s+\w+)',
            r'\b(Google Cloud\s+\w+)',
            r'\b(Microsoft Certified\s+\w+)',
            r'\b(Certified\s+\w+\s+Professional)',
            r'\b(PMP|CAPM|CISSP|CEH)\b',
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            certs.extend(matches)
        
        return list(set(certs))
    
    def _estimate_experience_years(self, text: str) -> float:
        """Estimate years of experience"""
        # Look for explicit mention
        years_match = re.search(r'(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?|y\.?)\s+(?:of\s+)?(?:experience|exp\.?)', text, re.IGNORECASE)
        if years_match:
            return float(years_match.group(1))
        
        # Estimate from job history
        experiences = self._extract_experience(text)
        if experiences:
            # Rough estimate: count jobs * 2.5 years average
            return len(experiences) * 2.5
        
        return 0.0


# Singleton
resume_parser = ResumeParser()
