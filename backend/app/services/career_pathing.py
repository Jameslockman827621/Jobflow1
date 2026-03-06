"""
Career Pathing Service

Analyzes user's profile and provides:
- Career progression recommendations
- Skill gap analysis
- Learning resources
- Salary trajectory
- Role transitions
"""

from typing import List, Dict, Optional
from datetime import datetime


class CareerPathingService:
    """Provide career guidance and pathing recommendations"""
    
    # Career progression paths by role
    CAREER_PATHS = {
        "software engineer": {
            "progression": [
                {"title": "Junior Engineer", "years": "0-2", "salary_range": "$60k-$90k"},
                {"title": "Mid-Level Engineer", "years": "2-5", "salary_range": "$90k-$140k"},
                {"title": "Senior Engineer", "years": "5-8", "salary_range": "$140k-$200k"},
                {"title": "Staff Engineer", "years": "8-12", "salary_range": "$200k-$300k"},
                {"title": "Principal Engineer", "years": "12+", "salary_range": "$300k-$500k"},
            ],
            "transitions": [
                {"role": "Engineering Manager", "skills_needed": ["Leadership", "People Management", "Strategy"]},
                {"role": "Product Manager", "skills_needed": ["Product Sense", "Communication", "Strategy"]},
                {"role": "Solutions Architect", "skills_needed": ["System Design", "Communication", "Cloud"]},
            ],
        },
        "product manager": {
            "progression": [
                {"title": "Associate PM", "years": "0-2", "salary_range": "$70k-$100k"},
                {"title": "PM", "years": "2-5", "salary_range": "$100k-$150k"},
                {"title": "Senior PM", "years": "5-8", "salary_range": "$150k-$220k"},
                {"title": "Group PM", "years": "8-12", "salary_range": "$220k-$350k"},
                {"title": "VP Product", "years": "12+", "salary_range": "$350k-$600k"},
            ],
            "transitions": [
                {"role": "Product Leader", "skills_needed": ["Strategy", "Leadership", "Vision"]},
                {"role": "Founder", "skills_needed": ["Vision", "Fundraising", "Execution"]},
                {"role": "Consulting", "skills_needed": ["Communication", "Analysis", "Presentation"]},
            ],
        },
        "data scientist": {
            "progression": [
                {"title": "Junior Data Scientist", "years": "0-2", "salary_range": "$70k-$100k"},
                {"title": "Data Scientist", "years": "2-5", "salary_range": "$100k-$150k"},
                {"title": "Senior Data Scientist", "years": "5-8", "salary_range": "$150k-$220k"},
                {"title": "Staff Data Scientist", "years": "8-12", "salary_range": "$220k-$350k"},
                {"title": "Principal DS / ML Lead", "years": "12+", "salary_range": "$350k-$550k"},
            ],
            "transitions": [
                {"role": "ML Engineer", "skills_needed": ["Software Engineering", "MLOps", "Deployment"]},
                {"role": "Analytics Manager", "skills_needed": ["Leadership", "Strategy", "Communication"]},
                {"role": "AI Research", "skills_needed": ["Deep Learning", "Research", "Publications"]},
            ],
        },
    }
    
    # Skills required for each level
    SKILL_REQUIREMENTS = {
        "Junior": ["Basic technical skills", "Willingness to learn", "Teamwork"],
        "Mid": ["Independent execution", "Mentoring juniors", "System design basics"],
        "Senior": ["Technical leadership", "Complex problem solving", "Cross-team collaboration"],
        "Staff": ["Org-wide impact", "Strategic thinking", "Technical vision"],
        "Principal": ["Industry recognition", "Long-term strategy", "Multiple teams leadership"],
    }
    
    # Learning resources by skill
    LEARNING_RESOURCES = {
        "System Design": [
            {"title": "Grokking System Design", "type": "course", "url": "https://educative.io"},
            {"title": "Designing Data-Intensive Applications", "type": "book", "author": "Martin Kleppmann"},
        ],
        "Leadership": [
            {"title": "The Manager's Path", "type": "book", "author": "Camille Fournier"},
            {"title": "High Output Management", "type": "book", "author": "Andrew Grove"},
        ],
        "Python": [
            {"title": "Fluent Python", "type": "book", "author": "Luciano Ramalho"},
            {"title": "Python for Data Analysis", "type": "book", "author": "Wes McKinney"},
        ],
    }
    
    def analyze_profile(self, user_profile: Dict) -> Dict:
        """Analyze user's profile and generate career recommendations"""
        role = (user_profile.get("current_title") or "").lower()
        years_exp = user_profile.get("years_of_experience", 0)
        skills = [s.get("name", "").lower() for s in user_profile.get("skills", [])]
        
        # Find matching career path
        career_path = self._find_matching_career_path(role)
        
        # Determine current level
        current_level = self._determine_level(years_exp, career_path)
        
        # Calculate skill gaps
        skill_gaps = self._analyze_skill_gaps(skills, current_level)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(career_path, current_level, skill_gaps)
        
        # Salary trajectory
        salary_trajectory = self._calculate_salary_trajectory(career_path, years_exp)
        
        return {
            "current_level": current_level,
            "career_path": career_path,
            "skill_gaps": skill_gaps,
            "recommendations": recommendations,
            "salary_trajectory": salary_trajectory,
            "next_milestone": self._get_next_milestone(current_level, years_exp),
        }
    
    def _find_matching_career_path(self, role: str) -> Dict:
        """Find the best matching career path for a role"""
        role_lower = role.lower()
        
        for key, path in self.CAREER_PATHS.items():
            if key in role_lower or role_lower in key:
                return path
        
        # Default to software engineer path
        return self.CAREER_PATHS["software engineer"]
    
    def _determine_level(self, years_exp: float, career_path: Dict) -> str:
        """Determine current career level based on experience"""
        if years_exp < 2:
            return "Junior"
        elif years_exp < 5:
            return "Mid"
        elif years_exp < 8:
            return "Senior"
        elif years_exp < 12:
            return "Staff"
        else:
            return "Principal"
    
    def _analyze_skill_gaps(self, current_skills: List[str], level: str) -> List[Dict]:
        """Analyze gaps between current skills and level requirements"""
        required_skills = self.SKILL_REQUIREMENTS.get(level, [])
        
        gaps = []
        for req_skill in required_skills:
            # Simple keyword matching (would use AI in production)
            if not any(req_skill.lower().split()[0] in skill for skill in current_skills):
                gaps.append({
                    "skill": req_skill,
                    "importance": "high" if level in ["Senior", "Staff"] else "medium",
                    "resources": self.LEARNING_RESOURCES.get(req_skill, []),
                })
        
        return gaps
    
    def _generate_recommendations(self, career_path: Dict, level: str, skill_gaps: List) -> List[Dict]:
        """Generate actionable career recommendations"""
        recommendations = []
        
        # Skill development
        if skill_gaps:
            recommendations.append({
                "type": "skill_development",
                "priority": "high",
                "title": f"Focus on {level}-level skills",
                "description": f"Develop these key skills: {', '.join([g['skill'] for g in skill_gaps[:3]])}",
                "timeline": "3-6 months",
            })
        
        # Next role preparation
        progression = career_path.get("progression", [])
        current_idx = next((i for i, p in enumerate(progression) if level.lower() in p["title"].lower()), 0)
        
        if current_idx < len(progression) - 1:
            next_role = progression[current_idx + 1]
            recommendations.append({
                "type": "promotion_prep",
                "priority": "medium",
                "title": f"Prepare for {next_role['title']}",
                "description": f"Target salary: {next_role['salary_range']}",
                "timeline": "12-18 months",
            })
        
        # Network building
        recommendations.append({
            "type": "networking",
            "priority": "medium",
            "title": "Build your professional network",
            "description": "Attend meetups, contribute to open source, write technical content",
            "timeline": "Ongoing",
        })
        
        return recommendations
    
    def _calculate_salary_trajectory(self, career_path: Dict, years_exp: float) -> List[Dict]:
        """Calculate projected salary growth"""
        progression = career_path.get("progression", [])
        trajectory = []
        
        for stage in progression:
            years = stage["years"]
            salary = stage["salary_range"]
            
            trajectory.append({
                "years": years,
                "title": stage["title"],
                "salary_range": salary,
            })
        
        return trajectory
    
    def _get_next_milestone(self, level: str, years_exp: float) -> Dict:
        """Get the next career milestone"""
        milestones = {
            "Junior": {
                "title": "Reach Mid-Level",
                "requirements": [
                    "Lead a small project independently",
                    "Mentor a junior engineer",
                    "Master your team's tech stack",
                ],
                "timeline": "12-24 months",
            },
            "Mid": {
                "title": "Reach Senior",
                "requirements": [
                    "Design and deliver complex systems",
                    "Become go-to person for your domain",
                    "Start mentoring others regularly",
                ],
                "timeline": "18-36 months",
            },
            "Senior": {
                "title": "Reach Staff",
                "requirements": [
                    "Drive org-wide technical initiatives",
                    "Develop technical strategy",
                    "Influence beyond your team",
                ],
                "timeline": "24-48 months",
            },
            "Staff": {
                "title": "Reach Principal",
                "requirements": [
                    "Set long-term technical vision",
                    "Industry recognition",
                    "Lead multiple teams",
                ],
                "timeline": "36-60 months",
            },
            "Principal": {
                "title": "Continue Growth",
                "requirements": [
                    "Expand impact",
                    "Consider executive track",
                    "Build legacy",
                ],
                "timeline": "Ongoing",
            },
        }
        
        return milestones.get(level, milestones["Mid"])


# Singleton
career_pathing = CareerPathingService()
