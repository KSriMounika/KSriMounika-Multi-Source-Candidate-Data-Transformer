from dataclasses import dataclass, field
from typing import List, Optional, Generic, TypeVar, Dict, Any

T = TypeVar('T')

@dataclass
class Provenance:
    """Tracks where a specific piece of data came from."""
    source: str  # e.g., 'CSV' or 'Resume PDF'
    extraction_method: str  # e.g., 'regex', 'direct_mapping'

@dataclass
class TrackedField(Generic[T]):
    """
    A wrapper for any field value that also stores its provenance and confidence.
    Using generics allows us to enforce the type of the underlying value (e.g., str, list).
    """
    value: Optional[T] = None
    provenance: List[Provenance] = field(default_factory=list)
    confidence: float = 0.0

@dataclass
class Location:
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None

@dataclass
class Links:
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    other: List[str] = field(default_factory=list)

@dataclass
class Skill:
    name: str
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)

@dataclass
class Experience:
    company: Optional[str] = None
    title: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    summary: Optional[str] = None

@dataclass
class Education:
    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    end_year: Optional[int] = None

@dataclass
class CandidateProfile:
    """The internal canonical representation of a candidate."""
    candidate_id: TrackedField[str] = field(default_factory=TrackedField)
    full_name: TrackedField[str] = field(default_factory=TrackedField)
    emails: TrackedField[List[str]] = field(default_factory=lambda: TrackedField(value=[]))
    phones: TrackedField[List[str]] = field(default_factory=lambda: TrackedField(value=[]))
    location: TrackedField[Location] = field(default_factory=lambda: TrackedField(value=Location()))
    links: TrackedField[Links] = field(default_factory=lambda: TrackedField(value=Links()))
    headline: TrackedField[str] = field(default_factory=TrackedField)
    years_experience: TrackedField[float] = field(default_factory=TrackedField)
    
    # Complex fields
    skills: TrackedField[List[Skill]] = field(default_factory=lambda: TrackedField(value=[]))
    experience: TrackedField[List[Experience]] = field(default_factory=lambda: TrackedField(value=[]))
    education: TrackedField[List[Education]] = field(default_factory=lambda: TrackedField(value=[]))
    
    overall_confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """A simple helper to convert the canonical model to a dictionary if needed."""
        # We will implement a more robust projection layer later, 
        # but this is useful for basic debugging.
        pass
