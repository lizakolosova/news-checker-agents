"""Tests for main agent."""

import pytest
from models import ClaimType
from config import ClaimExtractionConfig
from agent import ClaimExtractionAgent


class TestClaimExtractionAgent:
    """Test ClaimExtractionAgent class."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config is not None
        assert agent.patterns is not None
        assert agent.entity_extractor is not None
        assert agent.temporal_extractor is not None
        assert agent.numerical_extractor is not None

    def test_extract_claims_basic(self, agent):
        """Test basic claim extraction."""
        text = "The unemployment rate is 3.5%."
        claims = agent.extract_claims(text)

        assert len(claims) > 0
        assert any("3.5" in claim.text for claim in claims)

    def test_extract_statistical_claim(self, agent):
        """Test extraction of statistical claims."""
        text = "The company reported 85% growth in revenue."
        claims = agent.extract_claims(text)

        claims_with_numbers = [c for c in claims if c.numerical_data]
        assert len(claims_with_numbers) > 0

    def test_extract_attribution_claim(self, agent):
        """Test extraction of attribution claims."""
        text = "President Biden said the economy is strong."
        claims = agent.extract_claims(text)

        attribution_claims = [c for c in claims if c.claim_type == ClaimType.ATTRIBUTION]
        assert len(attribution_claims) > 0

    def test_extract_temporal_claim(self, agent):
        """Test extraction of temporal claims."""
        text = "The event occurred on January 15, 2024."
        claims = agent.extract_claims(text)

        assert len(claims) > 0
        assert any(claim.temporal_markers for claim in claims)

    def test_confidence_filtering(self):
        """Test that low confidence claims are filtered."""

        config = ClaimExtractionConfig(min_confidence=0.8)
        agent = ClaimExtractionAgent(config)

        text = "Maybe this could possibly happen."
        claims = agent.extract_claims(text)

        assert all(claim.confidence >= 0.8 for claim in claims)

    def test_extracts_entities(self, agent):
        """Test that entities are extracted."""
        text = "President Biden met Secretary Johnson."
        claims = agent.extract_claims(text)

        assert len(claims) > 0
        assert any(claim.entities for claim in claims)

    def test_extracts_numerical_data(self, agent):
        """Test that numerical data is extracted."""
        text = "The rate increased to 5.5% last quarter."
        claims = agent.extract_claims(text)

        assert len(claims) > 0
        assert any(claim.numerical_data for claim in claims)

    def test_deduplication(self, agent):
        """Test claim deduplication."""
        text = """
        The unemployment rate is 5.2%. The unemployment rate is 5.2%.
        The unemployment rate is 5.2%.
        """
        claims = agent.extract_claims(text)

        assert len(claims) == 1

    def test_sub_claim_extraction(self, agent):
        """Test extraction of sub-claims."""
        text = "The economy grew by 5%, and unemployment fell to 3%."
        claims = agent.extract_claims(text)

        assert len(claims) >= 1
        assert any(claim.numerical_data for claim in claims)

    def test_metadata_preservation(self, agent):
        """Test that metadata is preserved."""
        metadata = {"source": "test.com", "date": "2024-01-15"}
        text = "The rate is 5%."
        claims = agent.extract_claims(text, article_metadata=metadata)

        if claims:
            assert claims[0].metadata["source"] == "test.com"
            assert claims[0].metadata["date"] == "2024-01-15"