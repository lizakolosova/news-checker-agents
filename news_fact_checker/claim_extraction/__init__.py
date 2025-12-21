from news_fact_checker.claim_extraction.agent import ClaimExtractionAgent
from news_fact_checker.claim_extraction.models import Claim, ClaimType, ClaimConfidence
from news_fact_checker.config import ClaimExtractionConfig, DEFAULT_CONFIG

__version__ = "1.0.0"
__all__ = [
    "ClaimExtractionAgent",
    "Claim",
    "ClaimType",
    "ClaimConfidence",
    "ClaimExtractionConfig",
    "DEFAULT_CONFIG"
]