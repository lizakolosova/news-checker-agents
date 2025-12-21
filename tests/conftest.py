"""Pytest fixtures for claim claim_extraction tests."""

import sys
from pathlib import Path

# Add news_fact_checker to path
sys.path.insert(0, str(Path(__file__).parent.parent / "news_fact_checker"))

import pytest
from news_fact_checker.claim_extraction.models import Claim, ClaimType

from news_fact_checker.claim_extraction.patterns import ClaimPatterns
from news_fact_checker.claim_extraction.extractors import EntityExtractor, TemporalExtractor, NumberExtractor
from news_fact_checker.claim_extraction.agent import ClaimExtractionAgent
from news_fact_checker.config import ClaimExtractionConfig


@pytest.fixture
def sample_article():
    """Sample news article for testing."""
    return """
    The unemployment rate fell to 3.5% in December 2023, according to the Bureau 
    of Labor Statistics. This represents a significant decrease compared to the 
    previous year. President Smith stated that the economy added 250,000 jobs 
    last month. The Federal Reserve announced yesterday that it would maintain 
    interest rates at current levels. Inflation has decreased from 9.1% to 3.2% 
    over the past year.
    """


@pytest.fixture
def simple_sentences():
    """Simple test sentences."""
    return [
        "The unemployment rate is 3.5%.",
        "President Biden said the economy is strong.",
        "The company reported $1.2 billion in revenue.",
        "This happened on January 15, 2024.",
        "The policy caused unemployment to rise."
    ]


@pytest.fixture
def claim_patterns():
    """ClaimPatterns instance."""
    return ClaimPatterns()


@pytest.fixture
def entity_extractor(claim_patterns):
    """EntityExtractor instance."""
    return EntityExtractor(claim_patterns)


@pytest.fixture
def temporal_extractor(claim_patterns):
    """TemporalExtractor instance."""
    return TemporalExtractor(claim_patterns)


@pytest.fixture
def numerical_extractor(claim_patterns):
    """NumericalExtractor instance."""
    return NumberExtractor(claim_patterns)


@pytest.fixture
def test_config():
    """Test configuration."""
    return ClaimExtractionConfig(
        min_confidence=0.4,
        similarity_threshold=0.85,
        context_window=1
    )


@pytest.fixture
def agent(test_config):
    """ClaimExtractionAgent instance."""
    return ClaimExtractionAgent(test_config)


@pytest.fixture
def sample_claim():
    """Sample claim for testing."""
    return Claim(
        text="The unemployment rate is 3.5%.",
        claim_type=ClaimType.STATISTICAL,
        confidence=0.85,
        context="Previous context. The unemployment rate is 3.5%. Next context.",
        source_sentence="The unemployment rate is 3.5%.",
        entities=["Bureau"],
        temporal_markers=["December 2023"],
        numerical_data=[{"value": "3.5%", "context_before": "rate is", "context_after": ""}],
        metadata={"source": "test"}
    )