from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any


class VerdictRating(Enum):
    TRUE = "true"
    MOSTLY_TRUE = "mostly_true"
    HALF_TRUE = "half_true"
    MOSTLY_FALSE = "mostly_false"
    FALSE = "false"
    UNVERIFIABLE = "unverifiable"


@dataclass
class VerdictResult:
    claim_id: str
    claim_text: str
    rating: VerdictRating
    confidence: float
    explanation: str
    supporting_evidence_count: int
    refuting_evidence_count: int
    evidence_quality: float
    overall_credibility: float
    key_sources: List[Dict[str, str]]
    metadata: Dict[str, Any]