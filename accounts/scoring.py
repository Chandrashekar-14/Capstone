# accounts/scoring.py
"""
Unified Readiness Score Calculation System
Addresses: inconsistent scoring, hardcoded weights, no role-specific customization

Now supports:
- Dynamic weights learned from real placement data (via ML)
- Role-specific weights for targeted preparation
- Fallback to default weights if no ML training done
"""

from typing import Dict, Optional
from .models import Student
from django.core.cache import cache

# Default weights for general readiness score
DEFAULT_WEIGHTS = {
    'skills': 0.25,      # Technical skills (highest priority)
    'academics': 0.20,   # Academic performance
    'practice': 0.20,    # Coding practice/problem solving
    'projects': 0.20,    # Project experience
    'aptitude': 0.15     # Aptitude/problem-solving tests
}

# Role-specific weight adjustments
ROLE_WEIGHTS = {
    'Software Engineer': {
        'skills': 0.30,      # Higher technical skills
        'practice': 0.25,    # More coding practice
        'projects': 0.20,    # Project experience
        'academics': 0.15,   # Academic foundation
        'aptitude': 0.10     # Basic aptitude
    },
    'Data Scientist': {
        'academics': 0.25,   # Strong academic background
        'skills': 0.25,      # Technical skills (Python, ML)
        'practice': 0.20,    # Data analysis practice
        'projects': 0.15,    # Data projects
        'aptitude': 0.15     # Analytical aptitude
    },
    'Web Developer': {
        'skills': 0.30,      # Frontend/backend skills
        'projects': 0.25,    # Portfolio projects
        'practice': 0.20,    # Development practice
        'academics': 0.15,   # Basic academics
        'aptitude': 0.10     # Logical thinking
    },
    'AI Engineer': {
        'skills': 0.28,      # AI/ML technical skills
        'academics': 0.22,   # Mathematical foundation
        'practice': 0.20,    # ML practice
        'projects': 0.18,    # AI projects
        'aptitude': 0.12     # Analytical aptitude
    },
    'System Administrator': {
        'skills': 0.28,      # System/networking skills
        'practice': 0.25,    # Hands-on experience
        'academics': 0.20,   # Computer science basics
        'projects': 0.17,    # Infrastructure projects
        'aptitude': 0.10     # Troubleshooting aptitude
    }
}

def calculate_readiness_score(student: Student, target_role: Optional[str] = None) -> float:
    """
    Calculate readiness score using consistent weighted formula

    Args:
        student: Student instance
        target_role: Optional role for customized weights

    Returns:
        float: Readiness score (0-100)
    """
    # Try to get ML-optimized weights first
    optimal_weights = cache.get('optimal_weights')
    
    if optimal_weights and not target_role:
        # Use AI-learned weights if no specific role target
        weights = optimal_weights
    else:
        # Get appropriate weights
        weights = ROLE_WEIGHTS.get(target_role, DEFAULT_WEIGHTS)

    # Calculate weighted score
    score = (
        student.skills * weights['skills'] +
        student.academics * weights['academics'] +
        student.practice * weights['practice'] +
        student.projects * weights['projects'] +
        student.aptitude * weights['aptitude']
    )

    return round(score, 2)

def get_readiness_status(score: float) -> str:
    """
    Get status string based on readiness score

    Args:
        score: Readiness score (0-100)

    Returns:
        str: Status message
    """
    if score > 75:
        return "Placement Ready ✅"
    elif score > 50:
        return "Moderate ⚠️"
    else:
        return "Needs Improvement ❌"

def get_available_roles() -> list:
    """
    Get list of available roles for customization

    Returns:
        list: Role names
    """
    return list(ROLE_WEIGHTS.keys())

def get_role_weights(role: str) -> Dict[str, float]:
    """
    Get weights for a specific role

    Args:
        role: Role name

    Returns:
        dict: Weight mapping
    """
    return ROLE_WEIGHTS.get(role, DEFAULT_WEIGHTS)

def calculate_average_readiness(students, target_role: Optional[str] = None) -> float:
    """
    Calculate average readiness score for a group of students

    Args:
        students: QuerySet or list of Student objects
        target_role: Optional role for customized weights

    Returns:
        float: Average readiness score
    """
    if not students:
        return 0.0

    total_score = 0
    for student in students:
        total_score += calculate_readiness_score(student, target_role)

    return round(total_score / len(students), 2)