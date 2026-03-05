"""
Job-User Matching Service

Matches jobs to users based on:
- Skills overlap
- Seniority level
- Location preferences
- Salary expectations
- Industry/role preferences
"""

from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.profile import UserProfile, Skill


class JobMatcher:
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_match_score(self, user_profile: UserProfile, job: Job) -> float:
        """
        Calculate match score (0-100) for a user-job pair.
        
        Factors:
        - Skills match (40%)
        - Seniority match (20%)
        - Location/remote match (20%)
        - Salary match (20%)
        """
        scores = []
        weights = []
        
        # Skills match (40%)
        skills_score = self._skills_match(user_profile, job)
        scores.append(skills_score)
        weights.append(40)
        
        # Seniority match (20%)
        seniority_score = self._seniority_match(user_profile, job)
        scores.append(seniority_score)
        weights.append(20)
        
        # Location/remote match (20%)
        location_score = self._location_match(user_profile, job)
        scores.append(location_score)
        weights.append(20)
        
        # Salary match (20%)
        salary_score = self._salary_match(user_profile, job)
        scores.append(salary_score)
        weights.append(20)
        
        # Weighted average
        total_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        return round(total_score, 2)
    
    def _skills_match(self, profile: UserProfile, job: Job) -> float:
        """Calculate skills overlap (0-100)"""
        if not profile.skills and not job.skills_required:
            return 50  # Neutral if no data
        
        user_skills = set(s.name.lower() for s in profile.skills)
        job_skills = set(s.lower() for s in job.skills_required) if job.skills_required else set()
        
        if not job_skills:
            return 50  # No job requirements listed
        
        if not user_skills:
            return 0  # User has no skills listed
        
        overlap = user_skills & job_skills
        match_ratio = len(overlap) / len(job_skills)
        return round(match_ratio * 100, 2)
    
    def _seniority_match(self, profile: UserProfile, job: Job) -> float:
        """Check seniority alignment (0-100)"""
        seniority_levels = ["entry", "mid", "senior", "lead", "executive"]
        
        user_level = self._estimate_user_seniority(profile)
        job_level = job.seniority.lower() if job.seniority else None
        
        if not job_level or not user_level:
            return 50  # Neutral
        
        try:
            user_idx = seniority_levels.index(user_level)
            job_idx = seniority_levels.index(job_level)
            
            # Perfect match
            if user_idx == job_idx:
                return 100
            
            # One level off is okay
            diff = abs(user_idx - job_idx)
            if diff == 1:
                return 70
            
            # Two levels off
            if diff == 2:
                return 40
            
            # Too far apart
            return 10
        except ValueError:
            return 50
    
    def _estimate_user_seniority(self, profile: UserProfile) -> Optional[str]:
        """Estimate user's seniority from experience"""
        if not profile.years_of_experience:
            return None
        
        years = profile.years_of_experience
        if years < 2:
            return "entry"
        elif years < 5:
            return "mid"
        elif years < 8:
            return "senior"
        elif years < 12:
            return "lead"
        else:
            return "executive"
    
    def _location_match(self, profile: UserProfile, job: Job) -> float:
        """Check location compatibility (0-100)"""
        # Remote job - always good
        if job.remote and profile.remote_only:
            return 100
        
        if job.remote and not profile.remote_only:
            return 80  # Still good
        
        if job.hybrid:
            return 60  # Okay
        
        # Check location match
        if profile.location and job.location:
            # Simple string match (TODO: use geocoding)
            if profile.location.lower() in job.location.lower() or \
               job.location.lower() in profile.location.lower():
                return 100
            
            # Check country
            if profile.preferred_countries:
                for country in profile.preferred_countries:
                    if country.lower() in job.location.lower():
                        return 80
        
        # No location preference from user
        if not profile.location:
            return 50
        
        return 20  # Location mismatch
    
    def _salary_match(self, profile: UserProfile, job: Job) -> float:
        """Check salary expectations (0-100)"""
        if not profile.min_salary and not profile.max_salary:
            return 50  # No preference
        
        if not job.min_salary and not job.max_salary:
            return 50  # No salary listed
        
        # Get user's expected range
        user_min = profile.min_salary or 0
        user_max = profile.max_salary or float('inf')
        
        # Get job's range
        job_min = job.min_salary or 0
        job_max = job.max_salary or float('inf')
        
        # Check overlap
        if job_max < user_min:
            return 0  # Job pays less than minimum
        
        if job_min > user_max:
            return 100  # Job pays more than expected (great!)
        
        # Calculate overlap percentage
        overlap_start = max(user_min, job_min)
        overlap_end = min(user_max, job_max)
        overlap = overlap_end - overlap_start
        
        user_range = user_max - user_min if user_max != float('inf') else job_max - job_min
        if user_range <= 0:
            return 100
        
        return round((overlap / user_range) * 100, 2)
    
    def get_top_matches(self, user_id: int, limit: int = 20) -> List[Tuple[Job, float]]:
        """Get top job matches for a user"""
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            return []
        
        # Get active jobs
        jobs = self.db.query(Job).filter(Job.is_active == True).all()
        
        # Score all jobs
        scored_jobs = []
        for job in jobs:
            score = self.calculate_match_score(profile, job)
            scored_jobs.append((job, score))
        
        # Sort by score descending
        scored_jobs.sort(key=lambda x: x[1], reverse=True)
        
        return scored_jobs[:limit]
