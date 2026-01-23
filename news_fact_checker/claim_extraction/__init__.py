from news_fact_checker.claim_extraction.agent import ClaimExtractionAgent
from news_fact_checker.claim_extraction.models import (
    Claim,
    ClaimType,
    ClaimConfidence,
    ArticleMetadata,
    ExtractionResult,
)
from news_fact_checker.claim_extraction.classifiers import ClaimClassifier
from news_fact_checker.claim_extraction.validators import VerifiabilityAssessor
from news_fact_checker.claim_extraction.extractors import (
    EntityExtractor,
    NumberExtractor,
    TemporalExtractor,
    FeatureExtractor,
)
from news_fact_checker.claim_extraction.processors import (
    SubClaimProcessor,
    ClaimDeduplicator,
)
from news_fact_checker.config import ClaimExtractionConfig, DEFAULT_CONFIG

__version__ = "2.0.0"

__all__ = [
    "ClaimExtractionAgent",

    "Claim",
    "ClaimType",
    "ClaimConfidence",
    "ArticleMetadata",
    "ExtractionResult",

    "ClaimClassifier",
    "VerifiabilityAssessor",
    "EntityExtractor",
    "NumberExtractor",
    "TemporalExtractor",
    "FeatureExtractor",
    "SubClaimProcessor",
    "ClaimDeduplicator",

    "ClaimExtractionConfig",
    "DEFAULT_CONFIG",
]