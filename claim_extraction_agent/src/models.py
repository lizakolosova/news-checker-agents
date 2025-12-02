"""Data models for claim extraction."""

import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum


class ClaimType(Enum):
    """Types of claims that can be extracted."""
    STATISTICAL = "statistical"
    TEMPORAL = "temporal"
    ATTRIBUTION = "attribution"
    CAUSAL = "causal"
    COMPARATIVE = "comparative"
    FACTUAL = "factual"


class ClaimConfidence(Enum):
    """Confidence levels for extracted claims."""
    HIGH = "high"  # >0.8
    MEDIUM = "medium"  # 0.5-0.8
    LOW = "low"  # <0.5


@dataclass
class Claim:
    """Represents an extracted claim from an article."""

    claim_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    claim_type: ClaimType = ClaimType.FACTUAL
    confidence: float = 0.0
    context: str = ""
    source_sentence: str = ""
    entities: List[str] = field(default_factory=list)
    temporal_markers: List[str] = field(default_factory=list)
    numerical_data: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def confidence_level(self) -> ClaimConfidence:
        """Get confidence level enum based on score."""
        if self.confidence > 0.8:
            return ClaimConfidence.HIGH
        elif self.confidence > 0.5:
            return ClaimConfidence.MEDIUM
        return ClaimConfidence.LOW

    def to_dict(self) -> Dict[str, Any]:
        """Convert claim to dictionary for serialization."""
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "claim_type": self.claim_type.value,
            "confidence": round(self.confidence, 3),
            "confidence_level": self.confidence_level.value,
            "context": self.context,
            "source_sentence": self.source_sentence,
            "entities": self.entities,
            "temporal_markers": self.temporal_markers,
            "numerical_data": self.numerical_data,
            "metadata": self.metadata
        }