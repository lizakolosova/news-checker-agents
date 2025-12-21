"""Tests for data models."""

import pytest
from models import Claim, ClaimType, ClaimConfidence


class TestClaimType:
    """Test ClaimType enum."""

    def test_claim_types_exist(self):
        """Test all claim types are defined."""
        assert ClaimType.STATISTICAL.value == "statistical"
        assert ClaimType.TEMPORAL.value == "temporal"
        assert ClaimType.ATTRIBUTION.value == "attribution"
        assert ClaimType.CAUSAL.value == "causal"
        assert ClaimType.COMPARATIVE.value == "comparative"
        assert ClaimType.FACTUAL.value == "factual"


class TestClaimConfidence:
    """Test ClaimConfidence enum."""

    def test_confidence_levels_exist(self):
        """Test all confidence levels are defined."""
        assert ClaimConfidence.HIGH.value == "high"
        assert ClaimConfidence.MEDIUM.value == "medium"
        assert ClaimConfidence.LOW.value == "low"


class TestClaim:
    """Test Claim dataclass."""

    def test_claim_initialization(self):
        """Test claim can be initialized."""
        claim = Claim(text="Test claim", confidence=0.8)
        assert claim.text == "Test claim"
        assert claim.confidence == 0.8
        assert claim.claim_type == ClaimType.FACTUAL
        assert claim.claim_id is not None

    def test_confidence_level_high(self):
        """Test high confidence level."""
        claim = Claim(text="Test", confidence=0.85)
        assert claim.confidence_level == ClaimConfidence.HIGH

    def test_confidence_level_medium(self):
        """Test medium confidence level."""
        claim = Claim(text="Test", confidence=0.65)
        assert claim.confidence_level == ClaimConfidence.MEDIUM

    def test_confidence_level_low(self):
        """Test low confidence level."""
        claim = Claim(text="Test", confidence=0.4)
        assert claim.confidence_level == ClaimConfidence.LOW

    def test_to_dict(self, sample_claim):
        """Test claim serialization to dict."""
        claim_dict = sample_claim.to_dict()

        assert isinstance(claim_dict, dict)
        assert claim_dict["text"] == sample_claim.text
        assert claim_dict["claim_type"] == "statistical"
        assert claim_dict["confidence"] == 0.85
        assert claim_dict["confidence_level"] == "high"
        assert "claim_id" in claim_dict
        assert "entities" in claim_dict

    def test_unique_claim_ids(self):
        """Test that each claim gets a unique ID."""
        claim1 = Claim(text="Test 1")
        claim2 = Claim(text="Test 2")

        assert claim1.claim_id != claim2.claim_id