"""Tests for regex patterns."""

import pytest
from patterns import ClaimPatterns


class TestClaimPatterns:
    """Test ClaimPatterns class."""

    def test_patterns_initialization(self, claim_patterns):
        """Test patterns are compiled on initialization."""
        assert claim_patterns.number_pattern is not None
        assert claim_patterns.date_pattern is not None
        assert claim_patterns.attribution_pattern is not None
        assert claim_patterns.causal_pattern is not None
        assert claim_patterns.comparative_pattern is not None
        assert claim_patterns.entity_pattern is not None

    def test_number_pattern_matches(self, claim_patterns):
        """Test number pattern matches various formats."""
        test_cases = [
            ("The rate is 3.5%", True),
            ("Population: 1,234,567", True),
            ("Cost is $45.99", True),
            ("5 million people", True),
            ("No numbers here", False)
        ]

        for text, should_match in test_cases:
            result = claim_patterns.number_pattern.search(text)
            assert (result is not None) == should_match, f"Failed for: {text}"

    def test_date_pattern_matches(self, claim_patterns):
        """Test date pattern matches various formats."""
        test_cases = [
            ("January 15, 2024", True),
            ("12/31/2023", True),
            ("2024", True),
            ("March 3 2025", True),
            ("no date here", False)
        ]

        for text, should_match in test_cases:
            result = claim_patterns.date_pattern.search(text)
            assert (result is not None) == should_match, f"Failed for: {text}"

    def test_attribution_pattern_matches(self, claim_patterns):
        """Test attribution pattern matches."""
        test_cases = [
            ("The president said that", True),
            ("According to sources", True),
            ("She claimed the data", True),
            ("The report stated clearly", True),
            ("No attribution", False)
        ]

        for text, should_match in test_cases:
            result = claim_patterns.attribution_pattern.search(text)
            assert (result is not None) == should_match, f"Failed for: {text}"

    def test_causal_pattern_matches(self, claim_patterns):
        """Test causal pattern matches."""
        test_cases = [
            ("This caused the problem", True),
            ("Due to the weather", True),
            ("As a result of policy", True),
            ("Led to increased costs", True),
            ("No causation", False)
        ]

        for text, should_match in test_cases:
            result = claim_patterns.causal_pattern.search(text)
            assert (result is not None) == should_match, f"Failed for: {text}"

    def test_comparative_pattern_matches(self, claim_patterns):
        """Test comparative pattern matches."""
        test_cases = [
            ("More than expected", True),
            ("Less than last year", True),
            ("Compared to baseline", True),
            ("Team A versus Team B", True),
            ("No comparison", False)
        ]

        for text, should_match in test_cases:
            result = claim_patterns.comparative_pattern.search(text)
            assert (result is not None) == should_match, f"Failed for: {text}"