from rapidfuzz import process, fuzz
from typing import Optional

# A canonical taxonomy of skills we want to map to.
CANONICAL_SKILLS = [
    "Python",
    "Java",
    "JavaScript",
    "Machine Learning",
    "React",
    "AWS",
    "Docker",
    "Kubernetes",
    "SQL",
    "Data Analysis"
]

# Explicit mappings for common abbreviations/variations
SKILL_MAP = {
    "ml": "Machine Learning",
    "machine-learning": "Machine Learning",
    "python3": "Python"
}

def normalize_skill(raw_skill: str, threshold: float = 80.0) -> Optional[str]:
    """
    Normalizes a skill string by first checking explicit mappings, 
    then fuzzy matching against a canonical taxonomy.
    """
    if not raw_skill or not isinstance(raw_skill, str):
        return None
        
    cleaned_skill = raw_skill.strip()
    cleaned_lower = cleaned_skill.lower()
    
    # 1. Check explicit map
    if cleaned_lower in SKILL_MAP:
        return SKILL_MAP[cleaned_lower]
    
    # Use rapidfuzz to find the closest match in our canonical list
    # extractOne returns (match_string, score, index)
    match = process.extractOne(
        cleaned_skill, 
        CANONICAL_SKILLS, 
        scorer=fuzz.WRatio
    )
    
    if match:
        best_match, score, _ = match
        if score >= threshold:
            return best_match
            
    # If no good match, return the title-cased raw string as a fallback
    return cleaned_skill.title()
