from news_fact_checker.evidence.agent import EvidenceEvaluationAgent
from news_fact_checker.evidence.models import (
    StanceResult,
    StanceLabel,
    ConsensusLevel,
    CredibilityTier,
    EvidenceSource,
    EvaluatedSource,
    EvaluationResult,
    DomainReputation,
    ConsensusMetrics,
)
from news_fact_checker.evidence.config import EvidenceConfig, DEFAULT_EVIDENCE_CONFIG
from news_fact_checker.evidence.credibility_scorer import CredibilityScorer
from news_fact_checker.evidence.quality_assessor import QualityAssessor
from news_fact_checker.evidence.consensus_detector import ConsensusDetector
from news_fact_checker.evidence.reasoning_generator import ReasoningGenerator
from news_fact_checker.evidence.stance_classifier import StanceClassifier
from news_fact_checker.evidence.scoring import (
    score_recency,
    score_fit,
    calculate_overall_credibility,
    calculate_average_quality,
    calculate_confidence,
)

__version__ = "2.0.0"

__all__ = [
    "EvidenceEvaluationAgent",
    "StanceResult",
    "StanceLabel",
    "ConsensusLevel",
    "CredibilityTier",
    "EvidenceSource",
    "EvaluatedSource",
    "EvaluationResult",
    "DomainReputation",
    "ConsensusMetrics",
    "EvidenceConfig",
    "DEFAULT_EVIDENCE_CONFIG",
    "CredibilityScorer",
    "QualityAssessor",
    "ConsensusDetector",
    "ReasoningGenerator",
    "StanceClassifier",
    "score_recency",
    "score_fit",
    "calculate_overall_credibility",
    "calculate_average_quality",
    "calculate_confidence",
]