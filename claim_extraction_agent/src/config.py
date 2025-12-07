"""Configuration settings for Claim Extraction Agent and Research Agent."""
import os
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

@dataclass
class ResearchConfig:
    """Configuration for Research Agent."""
    max_results: int = 5
    search_api_key: str = os.getenv("SERPER_API_KEY", "")
    search_api: str = "serper"
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    min_relevance: float = 0.6
    loglevel: str = "INFO"

DEFAULT_RESEARCH_CONFIG = ResearchConfig()