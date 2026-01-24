from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict
from enum import Enum


class StanceLabel(Enum):
    SUPPORTS = "supports"
    REFUTES = "refutes"
    UNCLEAR = "unclear"


class ConsensusLevel(Enum):
    STRONG_SUPPORT = "strong_support"
    STRONG_REFUTATION = "strong_refutation"
    LIKELY_TRUE = "likely_true"
    LIKELY_FALSE = "likely_false"
    MIXED = "mixed"
    INSUFFICIENT = "insufficient"


class CredibilityTier(Enum):
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3
    TIER_0 = 0


class EvidenceSource(TypedDict, total=False):
    source_url: str
    source_title: str
    snippet: str
    published_date: Optional[str]
    claim_id: str
    relevance_score: float


class EvaluatedSource(EvidenceSource, total=False):
    stance: str
    stance_confidence: float
    credibility_score: float
    quality_score: float
    recency_score: float
    evidence_fit: float
    final_score: float
    credibility_tier: int


class EvaluationResult(TypedDict):
    claim_id: str
    retrieval_status: str
    avg_evidence_fit: float
    overall_credibility: float
    evidence_quality: float
    consensus_level: str
    evaluated_sources: List[EvaluatedSource]
    confidence: float
    reasoning: str


@dataclass
class StanceResult:
    label: str
    confidence: float
    reason: str
    source: str = "deterministic"

    @property
    def stance_enum(self) -> StanceLabel:
        try:
            return StanceLabel(self.label)
        except ValueError:
            return StanceLabel.UNCLEAR


@dataclass
class DomainReputation:
    score: float
    explanation: str

    def __post_init__(self):
        self.score = max(0.0, min(1.0, self.score))


@dataclass
class ConsensusMetrics:
    support_ratio: float
    refute_ratio: float
    total_weight: float
    num_sources: int
    debug_counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "support_ratio": round(self.support_ratio, 3),
            "refute_ratio": round(self.refute_ratio, 3),
            "total_weight": round(self.total_weight, 3),
            "num_sources": self.num_sources,
            **self.debug_counts,
        }