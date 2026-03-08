"""
CV Builder Service - AI-powered resume generation
"""
import os
from typing import Dict, List, Optional
from datetime import datetime


class CVBuilderService:
    """AI-powered CV/Resume builder"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
    
    async def generate_summary(self, experience: List[Dict], skills: List[str], target_role: str) -> str:
        """
        Generate professional summary using AI
        
        Args:
            experience: List of work experiences
            skills: List of skills
            target_role: Target job title
            
        Returns:
            Professional summary text
        """
        if not self.openai_api_key:
            # Fallback template
            return self._generate_fallback_summary(experience, skills, target_role)
        
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_api_key)
            
            experience_text = "\n".join([
                f"- {exp.get('role', '')} at {exp.get('company', '')} ({exp.get('start_date', '')} - {exp.get('end_date', 'Present')})"
                for exp in experience
            ])
            
            skills_text = ", ".join(skills[:10])
            
            prompt = f"""Create a compelling 3-4 sentence professional summary for a job seeker targeting {target_role} roles.

Experience:
{experience_text}

Skills: {skills_text}

Write in first person, professional tone, highlight achievements and value proposition."""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional resume writer. Write concise, impactful summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"AI summary generation failed: {e}")
            return self._generate_fallback_summary(experience, skills, target_role)
    
    def _generate_fallback_summary(self, experience: List[Dict], skills: List[str], target_role: str) -> str:
        """Fallback summary without AI"""
        years_exp = len(experience) * 3  # Rough estimate
        top_skills = ", ".join(skills[:5]) if skills else "relevant skills"
        
        return f"Experienced professional with {years_exp}+ years in the industry, specializing in {top_skills}. Proven track record of delivering results in {target_role} positions. Seeking to leverage expertise in a challenging new opportunity."
    
    async def enhance_job_description(self, role: str, company: str, basic_description: str) -> str:
        """
        Enhance basic job description with AI to make it more impactful
        """
        if not self.openai_api_key:
            return basic_description
        
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_api_key)
            
            prompt = f"""Enhance this job description to be more impactful and achievement-oriented. 
Use action verbs and quantify results where possible. Keep it to 3-4 bullet points.

Role: {role}
Company: {company}
Description: {basic_description}

Output as bullet points only."""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional resume writer. Write impactful, concise bullet points."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"AI enhancement failed: {e}")
            return basic_description
    
    async def tailor_cv_for_job(self, cv_data: Dict, job_description: str) -> Dict:
        """
        Tailor CV content to match a specific job description
        """
        if not self.openai_api_key:
            return cv_data
        
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_api_key)
            
            prompt = f"""Tailor this CV summary to better match the following job description.
Highlight relevant skills and experience. Keep it concise (3-4 sentences).

CV Summary: {cv_data.get('summary', '')}

Job Description:
{job_description[:1000]}  # Limit to 1000 chars

Output only the tailored summary."""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional resume writer. Tailor resumes to job descriptions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200
            )
            
            tailored_cv = cv_data.copy()
            tailored_cv['summary'] = response.choices[0].message.content.strip()
            return tailored_cv
            
        except Exception as e:
            print(f"CV tailoring failed: {e}")
            return cv_data
    
    def validate_cv_completeness(self, cv_data: Dict) -> Dict:
        """
        Check CV completeness and return score + missing items
        """
        required_fields = ['full_name', 'email', 'summary']
        optional_fields = ['phone', 'location', 'linkedin_url', 'experience', 'education', 'skills']
        
        score = 0
        max_score = len(required_fields) + len(optional_fields)
        missing = []
        suggestions = []
        
        # Check required fields
        for field in required_fields:
            if cv_data.get(field):
                score += 1
            else:
                missing.append(field)
                suggestions.append(f"Add your {field.replace('_', ' ')}")
        
        # Check optional fields
        for field in optional_fields:
            if cv_data.get(field):
                score += 1
            else:
                suggestions.append(f"Consider adding {field.replace('_', ' ')}")
        
        completeness_score = (score / max_score) * 100
        
        return {
            "score": round(completeness_score, 1),
            "missing": missing,
            "suggestions": suggestions,
            "is_complete": completeness_score >= 80
        }


# Singleton instance
cv_builder_service = CVBuilderService()
