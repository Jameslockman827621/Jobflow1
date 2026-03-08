"""
Cover Letter Generator Service - AI-powered personalized cover letters
"""
import os
from typing import Dict, Optional


class CoverLetterGenerator:
    """AI-powered cover letter generator"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
    
    async def generate_cover_letter(
        self,
        cv_data: Dict,
        job_data: Dict,
        company_info: Optional[Dict] = None
    ) -> str:
        """
        Generate personalized cover letter using AI
        
        Args:
            cv_data: User's CV data
            job_data: Job description and requirements
            company_info: Optional company information
            
        Returns:
            Personalized cover letter text
        """
        if not self.openai_api_key:
            return self._generate_template_cover_letter(cv_data, job_data)
        
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_api_key)
            
            # Build prompt
            prompt = self._build_cover_letter_prompt(cv_data, job_data, company_info)
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional cover letter writer. Write compelling, personalized cover letters that are concise (250-350 words), specific, and highlight relevant experience. Avoid generic phrases."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"AI cover letter generation failed: {e}")
            return self._generate_template_cover_letter(cv_data, job_data)
    
    def _build_cover_letter_prompt(
        self,
        cv_data: Dict,
        job_data: Dict,
        company_info: Optional[Dict] = None
    ) -> str:
        """Build AI prompt for cover letter generation"""
        
        # Extract key info
        candidate_name = cv_data.get('full_name', '[Your Name]')
        candidate_email = cv_data.get('email', '[Your Email]')
        candidate_phone = cv_data.get('phone', '[Your Phone]')
        
        # Get most relevant experience
        experience = cv_data.get('experience', [])
        recent_role = experience[0] if experience else {}
        
        # Get skills
        skills = cv_data.get('skills', [])
        top_skills = ', '.join(skills[:5]) if skills else 'relevant skills'
        
        # Job info
        job_title = job_data.get('title', '[Job Title]')
        company_name = job_data.get('company', '[Company]')
        job_description = job_data.get('description', '')
        requirements = job_data.get('requirements', '')
        
        # Company info
        company_description = company_info.get('description', '') if company_info else ''
        company_values = company_info.get('values', '') if company_info else ''
        
        prompt = f"""Write a personalized cover letter for this job application:

**Candidate:**
Name: {candidate_name}
Email: {candidate_email}
Phone: {candidate_phone}
Current/Most Recent Role: {recent_role.get('role', 'N/A')} at {recent_role.get('company', 'N/A')}
Key Skills: {top_skills}

**Job:**
Title: {job_title}
Company: {company_name}
Description: {job_description[:500]}
Requirements: {requirements[:500]}

**Company:**
{company_description if company_description else 'No additional company information available'}
{company_values if company_values else ''}

**Instructions:**
- Write in first person
- Keep it 250-350 words
- Start with a compelling hook (not "I am writing to apply...")
- Highlight 2-3 most relevant experiences/skills
- Show enthusiasm for THIS specific company/role
- End with a confident call to action
- Professional but conversational tone
- Format with proper business letter structure

Output the cover letter only, no explanations."""

        return prompt
    
    def _generate_template_cover_letter(self, cv_data: Dict, job_data: Dict) -> str:
        """Fallback template-based cover letter"""
        
        candidate_name = cv_data.get('full_name', '[Your Name]')
        candidate_email = cv_data.get('email', '[Your Email]')
        job_title = job_data.get('title', '[Job Title]')
        company_name = job_data.get('company', '[Company]')
        skills = cv_data.get('skills', [])
        experience = cv_data.get('experience', [])
        
        return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company_name}. With my background in {', '.join(skills[:3]) if skills else 'the field'} and proven track record of delivering results, I am confident I would be a valuable addition to your team.

{f"In my current role at {experience[0].get('company', 'my company')} as {experience[0].get('role', 'my position')}," if experience else "Throughout my career,"} I have developed expertise that aligns well with the requirements of this position. My experience includes:

• Demonstrating strong problem-solving and analytical skills
• Collaborating effectively with cross-functional teams
• Delivering high-quality results under tight deadlines

What excites me most about {company_name} is your commitment to innovation and excellence. I am particularly drawn to this opportunity because it aligns perfectly with my career goals and allows me to leverage my skills in meaningful ways.

I would welcome the opportunity to discuss how my background, skills, and enthusiasm would benefit {company_name}. Thank you for considering my application.

Sincerely,
{candidate_name}
{candidate_email}
{cv_data.get('phone', '')}
"""
    
    async def tailor_cover_letter(
        self,
        cover_letter: str,
        job_description: str,
        company_values: Optional[str] = None
    ) -> str:
        """
        Tailor existing cover letter for specific job/company
        """
        if not self.openai_api_key:
            return cover_letter
        
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_api_key)
            
            prompt = f"""Tailor this cover letter to better match the job description and company values.
Make it more specific and compelling. Keep the same length and structure.

**Current Cover Letter:**
{cover_letter}

**Job Description:**
{job_description[:800]}

{f"**Company Values:**\n{company_values}" if company_values else ""}

Output only the tailored cover letter."""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional cover letter writer. Tailor cover letters to specific jobs and companies."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Cover letter tailoring failed: {e}")
            return cover_letter
    
    def analyze_cover_letter(self, cover_letter: str) -> Dict:
        """
        Analyze cover letter quality and provide feedback
        """
        word_count = len(cover_letter.split())
        
        feedback = []
        score = 100
        
        # Check length
        if word_count < 200:
            feedback.append("Cover letter is too short. Aim for 250-350 words.")
            score -= 20
        elif word_count > 400:
            feedback.append("Cover letter is too long. Keep it under 350 words.")
            score -= 10
        
        # Check for generic phrases
        generic_phrases = [
            "i am writing to apply",
            "i believe i would be a good fit",
            "thank you for considering",
            "i am a team player"
        ]
        
        cover_letter_lower = cover_letter.lower()
        for phrase in generic_phrases:
            if phrase in cover_letter_lower:
                feedback.append(f"Avoid generic phrase: '{phrase}'. Be more specific.")
                score -= 5
        
        # Check for company name mention
        if "company" not in cover_letter_lower and len(cover_letter) > 50:
            feedback.append("Mention the company name to show personalization.")
            score -= 10
        
        return {
            "score": max(score, 0),
            "word_count": word_count,
            "feedback": feedback,
            "is_good": score >= 80
        }


# Singleton instance
cover_letter_generator = CoverLetterGenerator()
