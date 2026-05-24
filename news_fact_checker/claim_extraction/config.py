from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from news_fact_checker.claim_extraction.constants import (
    DEFAULT_SIMILARITY_THRESHOLD,
    DEFAULT_CONTEXT_WINDOW,
    MIN_SUB_CLAIM_WORDS,
    SUB_CLAIM_CONFIDENCE_MULTIPLIER,
    MIN_VERIFIABILITY_SCORE,
    MEDIUM_CONFIDENCE_THRESHOLD,
    VAGUE_REFERENTS,
)
from news_fact_checker.exceptions import InvalidConfigurationError


@dataclass
class ClaimExtractionConfig:

    min_confidence: float = MEDIUM_CONFIDENCE_THRESHOLD

    context_window: int = DEFAULT_CONTEXT_WINDOW

    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD

    min_sub_claim_words: int = MIN_SUB_CLAIM_WORDS
    sub_claim_confidence_multiplier: float = SUB_CLAIM_CONFIDENCE_MULTIPLIER

    drop_unverifiable: bool = True
    min_verifiability: float = MIN_VERIFIABILITY_SCORE
    drop_vague_referents: bool = True
    vague_referents: Tuple[str, ...] = field(default_factory=lambda: VAGUE_REFERENTS)

    enable_structured_logging: bool = True
    log_level: str = "INFO"

    def __post_init__(self):
        self._validate()

    def _validate(self) -> None:
        if not 0 <= self.min_confidence <= 1:
            raise InvalidConfigurationError(
                f"min_confidence must be between 0 and 1, got {self.min_confidence}"
            )

        if not 0 <= self.similarity_threshold <= 1:
            raise InvalidConfigurationError(
                f"similarity_threshold must be between 0 and 1, got {self.similarity_threshold}"
            )

        if self.context_window < 0:
            raise InvalidConfigurationError(
                f"context_window must be non-negative, got {self.context_window}"
            )

        if self.min_sub_claim_words < 1:
            raise InvalidConfigurationError(
                f"min_sub_claim_words must be positive, got {self.min_sub_claim_words}"
            )

        if not 0 <= self.sub_claim_confidence_multiplier <= 1:
            raise InvalidConfigurationError(
                f"sub_claim_confidence_multiplier must be between 0 and 1, got {self.sub_claim_confidence_multiplier}"
            )

        if not 0 <= self.min_verifiability <= 1:
            raise InvalidConfigurationError(
                f"min_verifiability must be between 0 and 1, got {self.min_verifiability}"
            )


DEFAULT_CONFIG = ClaimExtractionConfig()