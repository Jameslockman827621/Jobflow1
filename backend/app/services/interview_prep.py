"""
Interview Prep Service

Generates interview questions based on:
- Job role and seniority
- Company (culture, tech stack)
- User's experience level

Uses AI for personalized questions.
"""

from typing import List, Dict, Optional
from app.core.config import settings


class InterviewPrepService:
    """Generate interview questions and prep materials"""
    
    # Common questions by role
    ROLE_QUESTIONS = {
        "software engineer": [
            "Tell me about a challenging technical problem you solved recently.",
            "How do you approach debugging a complex issue?",
            "Describe a time you had to work with a difficult teammate.",
            "What's your experience with [TECH_STACK]?",
            "How do you stay current with new technologies?",
        ],
        "frontend engineer": [
            "Explain the difference between React state and props.",
            "How do you optimize frontend performance?",
            "Describe your approach to responsive design.",
            "What's your experience with state management libraries?",
            "How do you handle cross-browser compatibility issues?",
        ],
        "backend engineer": [
            "How do you design a scalable API?",
            "Explain database indexing and when you'd use it.",
            "Describe your experience with microservices.",
            "How do you handle authentication and authorization?",
            "What's your approach to caching?",
        ],
        "data scientist": [
            "Explain a machine learning project you've worked on.",
            "How do you handle imbalanced datasets?",
            "Describe your experience with feature engineering.",
            "How do you validate model performance?",
            "Explain overfitting and how to prevent it.",
        ],
        "product manager": [
            "How do you prioritize features in a roadmap?",
            "Describe a time you had to make a decision with incomplete data.",
            "How do you work with engineering teams?",
            "What metrics do you track for product success?",
            "How do you handle conflicting stakeholder requirements?",
        ],
    }
    
    # Behavioral questions (STAR method)
    BEHAVIORAL_QUESTIONS = [
        "Tell me about a time you failed and what you learned.",
        "Describe a situation where you had to meet a tight deadline.",
        "Give an example of when you showed leadership.",
        "Tell me about a time you disagreed with your manager.",
        "Describe a project where you had to work across teams.",
    ]
    
    # Company-specific questions (would be expanded with real data)
    COMPANY_QUESTIONS = {
        "google": [
            "How would you design Gmail for 1 billion users?",
            "Estimate the number of tennis balls that fit in a Boeing 747.",
        ],
        "meta": [
            "How would you improve Facebook's news feed algorithm?",
            "Design a system to detect fake accounts at scale.",
        ],
        "amazon": [
            "Tell me about a time you demonstrated customer obsession.",
            "Describe a time you dove deep into data to solve a problem.",
        ],
        "stripe": [
            "How would you design a payment processing system?",
            "What considerations are important for financial APIs?",
        ],
    }
    
    def generate_questions(
        self,
        role: str,
        company: Optional[str] = None,
        seniority: Optional[str] = None,
        tech_stack: Optional[List[str]] = None,
    ) -> Dict:
        """Generate interview questions for a specific role/company"""
        role_lower = role.lower()
        
        # Find matching role questions
        questions = []
        for key_role, qs in self.ROLE_QUESTIONS.items():
            if key_role in role_lower:
                questions.extend(qs)
                break
        
        # Add behavioral questions
        questions.extend(BEHAVIORAL_QUESTIONS[:3])  # Top 3 behavioral
        
        # Add company-specific if available
        company_questions = []
        if company:
            company_lower = company.lower()
            for key_company, qs in self.COMPANY_QUESTIONS.items():
                if key_company in company_lower:
                    company_questions = qs
                    break
        
        # Customize tech stack questions
        if tech_stack:
            for i, q in enumerate(questions[:]):
                if "[TECH_STACK]" in q:
                    questions[i] = q.replace("[TECH_STACK]", ", ".join(tech_stack[:3]))
        
        # Seniority adjustments
        if seniority in ["senior", "lead", "executive"]:
            questions.extend([
                "How do you mentor junior engineers?",
                "Describe your experience with technical decision-making.",
                "How do you balance technical debt with feature development?",
            ])
        
        return {
            "technical": questions[:5],
            "behavioral": BEHAVIORAL_QUESTIONS,
            "company_specific": company_questions,
            "tips": self._get_prep_tips(role, seniority),
        }
    
    def _get_prep_tips(self, role: str, seniority: Optional[str]) -> List[str]:
        """Get preparation tips"""
        tips = [
            "Research the company's products and recent news",
            "Prepare 2-3 questions to ask the interviewer",
            "Practice coding problems on LeetCode/HackerRank",
            "Review your past projects and be ready to discuss them",
        ]
        
        if "engineer" in role.lower():
            tips.extend([
                "Practice whiteboard coding",
                "Review system design fundamentals",
                "Be ready to explain your thought process out loud",
            ])
        
        if seniority in ["senior", "lead"]:
            tips.extend([
                "Prepare examples of leadership and mentorship",
                "Be ready to discuss architectural decisions",
                "Think about how you've influenced team culture",
            ])
        
        return tips
    
    def generate_company_research(self, company: str) -> Dict:
        """Generate company research summary"""
        # In production, this would fetch from API
        return {
            "company": company,
            "size": "Unknown (research on Glassdoor)",
            "culture": "Research on company website and Glassdoor",
            "recent_news": "Search Google News for recent updates",
            "interview_process": "Check Glassdoor for interview experiences",
            "tech_stack": "Check engineering blog or StackShare",
            "links": {
                "website": f"https://{company.lower()}.com",
                "glassdoor": f"https://glassdoor.com/Overview/Working-at-{company.replace(' ', '-')}",
                "linkedin": f"https://linkedin.com/company/{company.lower().replace(' ', '-')}",
            }
        }


# Singleton
interview_prep = InterviewPrepService()
