"""Configuration settings for Claim Extraction Agent."""

from dataclasses import dataclass


@dataclass
class ClaimExtractionConfig:
    """Configuration for claim extraction."""

    min_confidence: float = 0.5
    similarity_threshold: float = 0.85
    context_window: int = 1
    min_sub_claim_words: int = 4
    sub_claim_confidence_multiplier: float = 0.8
    log_level: str = "INFO"

DEFAULT_CONFIG = ClaimExtractionConfig()