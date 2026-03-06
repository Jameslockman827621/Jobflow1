"""
Job Deduplication Service

Prevents duplicate jobs from appearing in the system.

Deduplication Strategies:
1. **Exact Match (Same Source)**: source_id + external_id (database constraint)
2. **Cross-Source Match**: Same company + similar title + same location
3. **URL Match**: Same external_url across different sources
4. **Fuzzy Match**: Similar title + company (for slight variations)

Usage:
    from app.services.deduplication import JobDeduplicator
    
    deduplicator = JobDeduplicator(db)
    deduplicator.remove_duplicates()
"""

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session
from app.models.job import Job
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
import hashlib


class JobDeduplicator:
    """
    Handles job deduplication across multiple sources.
    
    Strategies (in order of confidence):
    1. URL match (highest confidence)
    2. Source + External ID (database constraint)
    3. Company + Title + Location (high confidence)
    4. Company + Fuzzy title match (medium confidence)
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_duplicates(self, limit: int = 1000) -> List[Tuple[int, List[int]]]:
        """
        Find duplicate jobs in the database.
        
        Returns:
            List of tuples: (keep_job_id, [duplicate_job_ids])
        """
        duplicates = []
        
        # Strategy 1: Same external_url across different sources
        url_duplicates = self._find_url_duplicates(limit)
        duplicates.extend(url_duplicates)
        
        # Strategy 2: Same company + title + location
        ctl_duplicates = self._find_company_title_location_duplicates(limit)
        duplicates.extend(ctl_duplicates)
        
        return duplicates
    
    def _find_url_duplicates(self, limit: int = 500) -> List[Tuple[int, List[int]]]:
        """
        Find jobs with identical external URLs.
        
        This is the highest confidence match - if two jobs have the same URL,
        they are definitely the same job.
        """
        subquery = self.db.query(
            Job.external_url,
            func.min(Job.id).label('keep_id'),
            func.array_agg(Job.id).label('all_ids')
        ).filter(
            Job.external_url.isnot(None),
            Job.is_active == True
        ).group_by(
            Job.external_url
        ).having(
            func.count(Job.id) > 1
        ).limit(limit).subquery()
        
        results = self.db.query(subquery).all()
        
        duplicates = []
        for row in results:
            all_ids = list(row.all_ids) if row.all_ids else []
            if len(all_ids) > 1:
                keep_id = row.keep_id
                duplicate_ids = [id for id in all_ids if id != keep_id]
                duplicates.append((keep_id, duplicate_ids))
        
        return duplicates
    
    def _find_company_title_location_duplicates(self, limit: int = 500) -> List[Tuple[int, List[int]]]:
        """
        Find jobs with same company + normalized title + location.
        
        Handles slight variations in job titles (e.g., "Senior Software Engineer" vs "Software Engineer (Senior)")
        """
        # Normalize titles for comparison
        jobs = self.db.query(Job).filter(
            Job.is_active == True,
            Job.company.isnot(None),
            Job.title.isnot(None),
            Job.location.isnot(None)
        ).limit(limit * 10).all()
        
        # Group by normalized key
        groups: Dict[str, List[int]] = {}
        
        for job in jobs:
            # Create normalized key
            key = self._create_dedup_key(job)
            
            if key not in groups:
                groups[key] = []
            groups[key].append(job.id)
        
        # Find groups with multiple jobs
        duplicates = []
        for key, job_ids in groups.items():
            if len(job_ids) > 1:
                # Keep the most recently scraped job
                jobs_in_group = self.db.query(Job).filter(Job.id.in_(job_ids)).all()
                sorted_jobs = sorted(jobs_in_group, key=lambda j: j.scraped_at or datetime.min, reverse=True)
                
                keep_id = sorted_jobs[0].id
                duplicate_ids = [j.id for j in sorted_jobs[1:]]
                duplicates.append((keep_id, duplicate_ids))
        
        return duplicates[:limit]
    
    def _create_dedup_key(self, job: Job) -> str:
        """
        Create a deduplication key from job attributes.
        
        Normalizes variations in:
        - Company names ("Google" vs "Google Inc." vs "Google LLC")
        - Job titles ("Senior Software Engineer" vs "Software Engineer, Senior")
        - Locations ("London, UK" vs "London, United Kingdom")
        """
        # Normalize company
        company = job.company.lower().strip()
        company = self._normalize_company(company)
        
        # Normalize title - extract core keywords
        title = job.title.lower().strip()
        title = self._normalize_title(title)
        
        # Normalize location
        location = job.location.lower().strip() if job.location else ""
        location = self._normalize_location(location)
        
        # Create hash
        key = f"{company}|{title}|{location}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _normalize_company(self, company: str) -> str:
        """Normalize company name variations"""
        # Remove common suffixes
        suffixes = [
            ' inc', ' inc.', ' ltd', ' ltd.', ' llc', ' llc.',
            ' limited', ' corporation', ' corp', ' corp.',
            ' company', ' co', ' co.', ' group', ' holdings'
        ]
        for suffix in suffixes:
            if company.endswith(suffix):
                company = company[:-len(suffix)]
        
        return company.strip()
    
    def _normalize_title(self, title: str) -> str:
        """
        Normalize job title by extracting core keywords.
        
        Removes:
        - Seniority indicators (senior, junior, lead, etc.)
        - Parenthetical content
        - Special characters
        """
        import re
        
        # Remove parenthetical content
        title = re.sub(r'\([^)]*\)', '', title)
        
        # Remove seniority indicators
        seniority_words = [
            'senior', 'sr', 'junior', 'jr', 'lead', 'principal',
            'staff', 'head', 'director', 'vp', 'chief', 'executive'
        ]
        for word in seniority_words:
            title = re.sub(rf'\b{word}\b', '', title, flags=re.IGNORECASE)
        
        # Remove special characters and extra spaces
        title = re.sub(r'[^\w\s]', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Sort words to handle reordered titles
        words = sorted(title.split())
        
        return ' '.join(words)
    
    def _normalize_location(self, location: str) -> str:
        """Normalize location variations"""
        # Country name mappings
        country_map = {
            'united kingdom': 'uk',
            'united states': 'us',
            'usa': 'us',
            'united states of america': 'us',
            'england': 'uk',
            'great britain': 'uk',
        }
        
        for full, abbrev in country_map.items():
            location = location.replace(full, abbrev)
        
        # Remove postal codes
        import re
        location = re.sub(r'\b\d{5}(?:-\d{4})?\b', '', location)  # US ZIP
        location = re.sub(r'\b[a-z]{1,2}\d{1,2}[a-z]?\s*\d?[a-z]{2}\b', '', location, flags=re.IGNORECASE)  # UK postcode
        
        return location.strip()
    
    def remove_duplicates(self, batch_size: int = 100) -> Dict:
        """
        Remove duplicate jobs, keeping the most recent/complete version.
        
        Args:
            batch_size: Number of duplicates to process per batch
        
        Returns:
            Dict with statistics
        """
        duplicates = self.find_duplicates(limit=batch_size)
        
        if not duplicates:
            return {"status": "completed", "removed": 0, "batches": 0}
        
        total_removed = 0
        batches = 0
        
        for keep_id, duplicate_ids in duplicates:
            # Delete duplicates
            deleted = self.db.query(Job).filter(
                Job.id.in_(duplicate_ids)
            ).delete(synchronize_session=False)
            
            total_removed += deleted
            batches += 1
            
            # Commit every 10 batches to avoid long transactions
            if batches % 10 == 0:
                self.db.commit()
        
        self.db.commit()
        
        return {
            "status": "completed",
            "removed": total_removed,
            "batches": batches,
            "duplicates_found": len(duplicates)
        }
    
    def prevent_duplicate_on_insert(self, job_data: Dict) -> Tuple[bool, str]:
        """
        Check if a job would be a duplicate before inserting.
        
        Args:
            job_data: Dict with job attributes
        
        Returns:
            Tuple of (is_duplicate, reason)
        """
        # Check 1: Same URL
        if job_data.get('external_url'):
            existing = self.db.query(Job).filter(
                Job.external_url == job_data['external_url'],
                Job.is_active == True
            ).first()
            
            if existing:
                return True, f"Duplicate URL (existing job #{existing.id})"
        
        # Check 2: Same source + external_id
        if job_data.get('source_id') and job_data.get('external_id'):
            existing = self.db.query(Job).filter(
                Job.source_id == job_data['source_id'],
                Job.external_id == job_data['external_id'],
                Job.is_active == True
            ).first()
            
            if existing:
                return True, f"Duplicate source ID (existing job #{existing.id})"
        
        # Check 3: Same company + title + location
        if all(k in job_data for k in ['company', 'title', 'location']):
            key = self._create_dedup_key_from_dict(job_data)
            
            # Find jobs with same key
            similar_jobs = self.db.query(Job).filter(
                Job.company.ilike(f"%{job_data['company']}%"),
                Job.is_active == True
            ).limit(100).all()
            
            for job in similar_jobs:
                if self._create_dedup_key(job) == key:
                    return True, f"Duplicate company/title/location (existing job #{job.id})"
        
        return False, ""
    
    def _create_dedup_key_from_dict(self, job_data: Dict) -> str:
        """Create dedup key from dict (for pre-insert checking)"""
        from app.models.job import Job
        
        # Create a temporary Job object
        temp_job = Job(
            company=job_data.get('company', ''),
            title=job_data.get('title', ''),
            location=job_data.get('location', '')
        )
        
        return self._create_dedup_key(temp_job)
    
    def get_duplicate_stats(self) -> Dict:
        """Get statistics about duplicates in the database"""
        total_jobs = self.db.query(func.count(Job.id)).filter(
            Job.is_active == True
        ).scalar()
        
        # Count jobs with duplicate URLs
        duplicate_urls = self.db.query(
            Job.external_url,
            func.count(Job.id).label('count')
        ).filter(
            Job.external_url.isnot(None),
            Job.is_active == True
        ).group_by(Job.external_url).having(
            func.count(Job.id) > 1
        ).all()
        
        total_url_dups = sum(row.count - 1 for row in duplicate_urls)
        
        return {
            "total_active_jobs": total_jobs,
            "duplicate_url_count": total_url_dups,
            "duplicate_percentage": (total_url_dups / total_jobs * 100) if total_jobs > 0 else 0,
            "unique_urls": self.db.query(func.count(func.distinct(Job.external_url))).filter(
                Job.external_url.isnot(None)
            ).scalar()
        }
