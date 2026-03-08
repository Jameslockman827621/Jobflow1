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
        Generate professional summary using AI - NO SLOP, just substance
        
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
                f"- {exp.get('role', '')} at {exp.get('company', '')} ({exp.get('start_date', '')} - {exp.get('end_date', 'Present')})\n  {exp.get('description', '')[:200]}"
                for exp in experience[:3]  # Last 3 roles max
            ])
            
            skills_text = ", ".join(skills[:10])
            
            # ANTI-SLOP PROMPT: Forces specific, measurable, real content
            prompt = f"""Write a professional summary for a {target_role} role.

EXPERIENCE:
{experience_text}

SKILLS: {skills_text}

RULES - NO AI SLOP:
❌ NO: "results-driven", "motivated professional", "proven track record", "excellent communication skills", "team player", "think outside the box", "go-getter", "self-starter"
❌ NO: Generic fluff, buzzwords, corporate jargon
✅ YES: Specific technologies, real achievements, measurable impact
✅ YES: Concrete skills, actual domains, real responsibilities
✅ YES: Direct, clear, substantive

FORMAT:
- 3-4 sentences max
- First person OK but not required
- Lead with strongest qualification
- Include 1-2 specific achievements if possible
- End with what they're seeking next

EXAMPLE OF GOOD:
"Software engineer with 6 years building backend systems in Python and Go. Built APIs serving 10M+ requests/day at Scale AI. Reduced database query times by 80% through indexing and caching. Seeking senior backend roles in fintech or infrastructure."

EXAMPLE OF BAD:
"Results-driven professional with proven track record of excellence. Excellent communicator and team player who thinks outside the box."

Write the summary. No intro, no explanation, just the summary."""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a no-nonsense resume writer. Write specific, substantive summaries. Zero fluff."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Post-process: Remove any remaining slop
            slop_phrases = [
                "results-driven", "highly motivated", "proven track record", 
                "excellent communication", "team player", "think outside the box",
                "go-getter", "self-starter", "detail-oriented", "ability to work"
            ]
            for phrase in slop_phrases:
                summary = summary.replace(phrase, "").replace("  ", " ")
            
            return summary.strip()
            
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
        Enhance basic job description with AI - REAL achievements, not fluff
        """
        if not self.openai_api_key:
            return basic_description
        
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_api_key)
            
            # ANTI-SLOP PROMPT for job descriptions
            prompt = f"""Transform this basic job description into 3-4 achievement-focused bullet points.

ROLE: {role}
COMPANY: {company}
BASIC DESCRIPTION: {basic_description}

RULES - NO AI SLOP:
❌ NO: "Responsible for", "Tasked with", "Duties included"
❌ NO: Vague claims without numbers
❌ NO: "Helped", "Assisted", "Worked on"
✅ YES: Start with strong action verbs (Built, Led, Created, Reduced, Increased, Launched)
✅ YES: Include numbers, percentages, scale wherever possible
✅ YES: Show impact, not just responsibilities

EXAMPLE GOOD:
• Built REST API serving 50K+ daily users using Python and FastAPI
• Reduced deployment time from 2 hours to 15 minutes with CI/CD pipeline
• Led team of 4 engineers to launch mobile app with 4.8★ App Store rating

EXAMPLE BAD:
• Responsible for developing APIs
• Helped with deployment processes
• Worked on mobile application team

Write 3-4 bullet points. No intro, no explanation."""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a resume writer. Write specific, measurable achievement bullets. Zero fluff."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"AI enhancement failed: {e}")
            return basic_description
    
    async def suggest_achievements(self, role: str, company: str, duration_months: int) -> List[str]:
        """
        Suggest realistic, measurable achievements for a role
        Helps users who struggle to quantify their impact
        """
        if not self.openai_api_key:
            return self._get_generic_achievement_suggestions(role)
        
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_api_key)
            
            prompt = f"""Suggest 5 realistic, measurable achievements for someone who worked as {role} at {company} for {duration_months} months.

RULES:
- Each should be specific and measurable (include numbers, %, $, time)
- Cover different areas: technical, leadership, business impact
- Realistic for the role level and company
- No generic fluff

FORMAT: Bullet points only, each 1-2 sentences.

EXAMPLE GOOD ACHIEVEMENTS:
• Reduced API response time from 500ms to 150ms through caching and query optimization
• Led migration from monolith to microservices, improving deployment frequency by 10x
• Mentored 3 junior engineers, all promoted within 12 months"""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a career coach. Suggest specific, measurable achievements."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400
            )
            
            suggestions = response.choices[0].message.content.strip().split('\n')
            return [s.strip().lstrip('•-').strip() for s in suggestions if s.strip()]
            
        except Exception as e:
            print(f"Achievement suggestion failed: {e}")
            return self._get_generic_achievement_suggestions(role)
    
    def _get_generic_achievement_suggestions(self, role: str) -> List[str]:
        """Fallback achievement suggestions"""
        return [
            "Reduced [metric] by X% through [specific action]",
            "Built [project/system] that served [number] users",
            "Led [initiative] resulting in [measurable outcome]",
            "Improved [process] efficiency by X%",
            "Mentored [number] team members who achieved [result]"
        ]
    
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
