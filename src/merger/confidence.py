from typing import List
from src.models.candidate import Provenance

# Base confidence scores based on the source's assumed reliability
SOURCE_BASE_CONFIDENCE = {
    "CSV": 0.90,
    "Resume": 0.80
}

def calculate_field_confidence(provenances: List[Provenance], has_conflict: bool = False) -> float:
    """
    Calculates the confidence score for a single field based on its provenance.
    
    Rules:
    - Base score comes from the source.
    - If found in multiple distinct sources, confidence increases.
    - If there was a conflict during merging, confidence decreases.
    """
    if not provenances:
        return 0.0
        
    # Extract unique source names
    sources = set(p.source for p in provenances)
    
    # Get the max base confidence from the available sources
    base_score = max((SOURCE_BASE_CONFIDENCE.get(src, 0.5) for src in sources), default=0.0)
    
    # Adjust score based on agreement/disagreement
    final_score = base_score
    
    if len(sources) > 1:
        # Found in both CSV and Resume! We are more confident.
        final_score = min(1.0, final_score + 0.05)
        
    if has_conflict:
        # There was a conflict (e.g., CSV had one name, Resume had another).
        # We resolved it, but our confidence is shaken.
        final_score = max(0.0, final_score - 0.20)
        
    return round(final_score, 2)

def calculate_overall_confidence(field_confidences: List[float]) -> float:
    """
    Calculates the overall confidence score for the entire candidate profile.
    Simple approach: average the confidences of all non-null fields.
    """
    if not field_confidences:
        return 0.0
    
    avg = sum(field_confidences) / len(field_confidences)
    return round(avg, 2)
