"""
Evidence Evaluation Agent Package
Assesses source credibility and evidence quality for fact-checking.
"""

from .evidence_agent import EvidenceEvaluationAgent
from .credibility_scorer import CredibilityScorer
from .quality_assessor import QualityAssessor
from .consensus_detector import ConsensusDetector
from .reasoning_generator import ReasoningGenerator

__version__ = "1.0.0"
__all__ = [
    "EvidenceEvaluationAgent",
    "CredibilityScorer",
    "QualityAssessor",
    "ConsensusDetector",
    "ReasoningGenerator"
]