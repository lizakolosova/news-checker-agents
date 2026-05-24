from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict
from enum import Enum


class ClaimType(Enum):
    STATISTICAL = "statistical"
    TEMPORAL = "temporal"
    ATTRIBUTION = "attribution"
    CAUSAL = "causal"
    COMPARATIVE = "comparative"
    FACTUAL = "factual"


class ClaimConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ArticleMetadata(TypedDict, total=False):
    source: str
    published_date: str
    author: str
    url: str
    title: str


class NumericalData(TypedDict):
    value: str
    start: int
    end: int


@dataclass
class Claim:
    claim_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    claim_type: ClaimType = ClaimType.FACTUAL
    confidence: float = 0.0
    context: str = ""
    source_sentence: str = ""
    entities: List[str] = field(default_factory=list)
    temporal_markers: List[str] = field(default_factory=list)
    numerical_data: List[NumericalData] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def confidence_level(self) -> ClaimConfidence:
        if self.confidence > 0.8:
            return ClaimConfidence.HIGH
        elif self.confidence > 0.5:
            return ClaimConfidence.MEDIUM
        return ClaimConfidence.LOW

    @property
    def is_high_confidence(self) -> bool:
        return self.confidence_level == ClaimConfidence.HIGH

    @property
    def is_sub_claim(self) -> bool:
        return self.metadata.get("is_sub_claim", False)

    @property
    def verifiability_score(self) -> Optional[float]:
        return self.metadata.get("verifiability_score")

    def to_dict(self) -> Dict[str, Any]:
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
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return (
            f"Claim(text='{self.text[:50]}...', "
            f"type={self.claim_type.value}, "
            f"confidence={self.confidence:.2f})"
        )


@dataclass
class ExtractionResult:
    claims: List[Claim] = field(default_factory=list)
    total_sentences: int = 0
    total_claims_extracted: int = 0
    high_confidence_claims: int = 0
    article_metadata: Optional[ArticleMetadata] = None
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def extraction_rate(self) -> float:
        if self.total_sentences == 0:
            return 0.0
        return self.total_claims_extracted / self.total_sentences

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claims": [claim.to_dict() for claim in self.claims],
            "total_sentences": self.total_sentences,
            "total_claims_extracted": self.total_claims_extracted,
            "high_confidence_claims": self.high_confidence_claims,
            "extraction_rate": round(self.extraction_rate, 3),
            "article_metadata": self.article_metadata,
            "extraction_metadata": self.extraction_metadata,
        }