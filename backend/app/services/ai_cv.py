"""
AI CV Tailoring Service

Uses LLM to:
- Tailor CV/resume to specific job descriptions
- Generate targeted cover letters
- Answer application questions
"""

from typing import Optional, Dict
from openai import OpenAI
from app.core.config import settings


class AINotConfiguredError(RuntimeError):
    """Raised when OPENAI_API_KEY is missing — never return fake CV/letter content."""


class AICVService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.model = settings.LLM_MODEL

    def _require_client(self) -> None:
        if not self.client:
            raise AINotConfiguredError(
                "OPENAI_API_KEY is not configured. AI CV/cover letter features are disabled."
            )
    
    def tailor_cv(self, resume_text: str, job_description: str, user_profile: Dict) -> str:
        """
        Tailor a CV/resume to match a specific job description.
        
        Highlights relevant skills and experience.
        Uses keywords from job description.
        """
        self._require_client()
        
        prompt = f"""You are an expert resume writer. Tailor this CV to the job description below.

USER PROFILE:
- Name: {user_profile.get('first_name', '')} {user_profile.get('last_name', '')}
- Current Title: {user_profile.get('current_title', '')}
- Years of Experience: {user_profile.get('years_of_experience', '')}
- Location: {user_profile.get('location', '')}

JOB DESCRIPTION:
{job_description}

ORIGINAL CV:
{resume_text}

TASK:
1. Highlight skills and experience that match the job requirements
2. Use keywords from the job description naturally
3. Reorder sections to emphasize most relevant experience
4. Keep it concise and professional
5. Maintain honesty - don't fabricate experience

Output only the tailored CV, no explanations."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except AINotConfiguredError:
            raise
        except Exception as e:
            raise RuntimeError(f"AI CV tailoring failed: {e}") from e
    
    def generate_cover_letter(
        self, 
        job_description: str, 
        company: str,
        user_profile: Dict
    ) -> str:
        """Generate a targeted cover letter"""
        self._require_client()
        
        prompt = f"""Write a compelling cover letter for this job application.

COMPANY: {company}

JOB DESCRIPTION:
{job_description}

CANDIDATE:
- Name: {user_profile.get('first_name', '')} {user_profile.get('last_name', '')}
- Current Title: {user_profile.get('current_title', '')}
- Years of Experience: {user_profile.get('years_of_experience', '')} years
- Key Skills: {', '.join(user_profile.get('skills', []))}
- Location: {user_profile.get('location', '')}

REQUIREMENTS:
1. Keep it under 300 words
2. Show enthusiasm for the company and role
3. Highlight 2-3 most relevant achievements
4. Explain why you're a great fit
5. Professional but personable tone
6. Include a call to action

Output only the cover letter, no explanations."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.5,
            )
            return response.choices[0].message.content
        except AINotConfiguredError:
            raise
        except Exception as e:
            raise RuntimeError(f"Cover letter generation failed: {e}") from e
    
    def answer_application_questions(
        self, 
        questions: Dict[str, str], 
        user_profile: Dict
    ) -> Dict[str, str]:
        """Generate answers to application-specific questions"""
        self._require_client()
        
        answers = {}
        for question_id, question_text in questions.items():
            prompt = f"""Answer this job application question based on the candidate's profile.

QUESTION: {question_text}

CANDIDATE PROFILE:
{user_profile}

Provide a concise, professional answer (2-3 sentences max). Be honest and specific."""

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.3,
                )
                answers[question_id] = response.choices[0].message.content
            except Exception as e:
                raise RuntimeError(f"AI question answer failed: {e}") from e
        
        return answers


# Singleton instance
ai_cv_service = AICVService()
