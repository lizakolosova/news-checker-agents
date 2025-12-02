"""
Claim Extraction Agent Package

A production-ready agent for extracting factual claims from news articles.
"""

from claim_extraction_agent.src.agent import ClaimExtractionAgent
from models import Claim, ClaimType, ClaimConfidence
from claim_extraction_agent.src.config import ClaimExtractionConfig, DEFAULT_CONFIG

__version__ = "1.0.0"
__all__ = [
    "ClaimExtractionAgent",
    "Claim",
    "ClaimType",
    "ClaimConfidence",
    "ClaimExtractionConfig",
    "DEFAULT_CONFIG"
]