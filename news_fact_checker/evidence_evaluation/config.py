from __future__ import annotations

from dataclasses import dataclass

from news_fact_checker.evidence_evaluation.constants import (
    DEFAULT_DOMAIN_WEIGHT,
    DEFAULT_QUALITY_WEIGHT,
    DEFAULT_RECENCY_WEIGHT,
    STRONG_CONSENSUS_THRESHOLD,
    LIKELY_CONSENSUS_THRESHOLD,
    MIXED_CONSENSUS_THRESHOLD,
)


@dataclass
class EvidenceConfig:
    domain_weight: float = DEFAULT_DOMAIN_WEIGHT
    quality_weight: float = DEFAULT_QUALITY_WEIGHT
    recency_weight: float = DEFAULT_RECENCY_WEIGHT

    strong_consensus_threshold: float = STRONG_CONSENSUS_THRESHOLD
    likely_consensus_threshold: float = LIKELY_CONSENSUS_THRESHOLD
    mixed_consensus_threshold: float = MIXED_CONSENSUS_THRESHOLD

    enable_llm_credibility: bool = False
    llm_model: str = "llama3"

    consensus_feedback_enabled: bool = True
    consensus_feedback_weight: float = 1.0
    consensus_feedback_step: float = 0.03

    def __post_init__(self):
        self._validate()

    def _validate(self):
        total_weight = self.domain_weight + self.quality_weight + self.recency_weight
        if not 0.99 <= total_weight <= 1.01:
            raise ValueError(
                f"Weights must sum to 1.0, got {total_weight:.3f}"
            )

        for name, value in [
            ("domain_weight", self.domain_weight),
            ("quality_weight", self.quality_weight),
            ("recency_weight", self.recency_weight),
        ]:
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1, got {value}")

        for name, value in [
            ("strong_consensus_threshold", self.strong_consensus_threshold),
            ("likely_consensus_threshold", self.likely_consensus_threshold),
            ("mixed_consensus_threshold", self.mixed_consensus_threshold),
        ]:
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1, got {value}")


DEFAULT_EVIDENCE_CONFIG = EvidenceConfig()