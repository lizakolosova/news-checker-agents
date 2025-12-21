"""Integration tests for the complete system."""

import pytest
from models import ClaimType


class TestIntegration:
    """Integration tests."""

    def test_full_article_extraction(self, agent, sample_article):
        """Test claim_extraction from full article."""
        claims = agent.extract_claims(sample_article)

        assert len(claims) >= 3

        statistical = [c for c in claims if c.claim_type == ClaimType.STATISTICAL]
        assert len(statistical) > 0

        assert all(0 <= c.confidence <= 1 for c in claims)

        assert any(c.entities for c in claims)

    def test_claim_serialization(self, agent, sample_article):
        """Test that claims can be serialized."""
        claims = agent.extract_claims(sample_article)

        for claim in claims:
            claim_dict = claim.to_dict()

            assert isinstance(claim_dict, dict)
            assert "claim_id" in claim_dict
            assert "text" in claim_dict
            assert "confidence" in claim_dict
            assert "claim_type" in claim_dict

    def test_empty_article(self, agent):
        """Test handling of empty article."""
        claims = agent.extract_claims("")
        assert claims == []

    def test_article_with_no_claims(self, agent):
        """Test article with no verifiable claims."""
        text = "Maybe this could happen. It might be true. Perhaps we'll see."
        claims = agent.extract_claims(text)

        assert len(claims) <= 1

    def test_complex_article(self, agent):
        """Test complex article with multiple claim types."""
        text = """
        On December 15, 2023, the Federal Reserve announced that inflation 
        decreased to 3.1%, according to official data. This represents a 
        significant decline compared to last year's 9.1%. Chairman Powell 
        stated that the policy changes caused the improvement. Economists 
        say this is higher than the target rate of 2%.
        """

        claims = agent.extract_claims(text)

        claim_types = {c.claim_type for c in claims}
        assert len(claim_types) >= 2

        confidences = {c.confidence_level for c in claims}
        assert len(confidences) >= 1

        assert any(c.temporal_markers for c in claims)

        assert any(c.numerical_data for c in claims)