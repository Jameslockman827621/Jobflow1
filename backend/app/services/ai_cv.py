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


class AICVService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.model = settings.LLM_MODEL
    
    def tailor_cv(self, resume_text: str, job_description: str, user_profile: Dict) -> str:
        """
        Tailor a CV/resume to match a specific job description.
        
        Highlights relevant skills and experience.
        Uses keywords from job description.
        """
        if not self.client:
            return self._mock_tailor_cv(resume_text, job_description)
        
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
        except Exception as e:
            print(f"AI CV tailoring error: {e}")
            return self._mock_tailor_cv(resume_text, job_description)
    
    def generate_cover_letter(
        self, 
        job_description: str, 
        company: str,
        user_profile: Dict
    ) -> str:
        """Generate a targeted cover letter"""
        if not self.client:
            return self._mock_cover_letter(job_description, company, user_profile)
        
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
        except Exception as e:
            print(f"Cover letter generation error: {e}")
            return self._mock_cover_letter(job_description, company, user_profile)
    
    def answer_application_questions(
        self, 
        questions: Dict[str, str], 
        user_profile: Dict
    ) -> Dict[str, str]:
        """Generate answers to application-specific questions"""
        if not self.client:
            return {q: f"[Answer to: {q}]" for q in questions.keys()}
        
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
                print(f"Error answering question: {e}")
                answers[question_id] = f"[Manual answer needed for: {question_text}]"
        
        return answers
    
    def _mock_tailor_cv(self, resume: str, job_desc: str) -> str:
        """Fallback when AI is not available"""
        return f"""[AI Not Configured - Original CV]

{resume}

---
Note: Configure OPENAI_API_KEY to enable AI-powered CV tailoring.
"""
    
    def _mock_cover_letter(self, job_desc: str, company: str, profile: Dict) -> str:
        """Fallback when AI is not available"""
        return f"""Dear Hiring Manager,

I am writing to express my interest in the position at {company}.

[AI Not Configured - This is a placeholder cover letter]

With my background and skills, I believe I would be a great fit for this role.

Thank you for considering my application.

Best regards,
{profile.get('first_name', '')} {profile.get('last_name', '')}

---
Note: Configure OPENAI_API_KEY to enable AI-powered cover letter generation.
"""


# Singleton instance
ai_cv_service = AICVService()
