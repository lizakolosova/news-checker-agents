"""Tests for extractors and utilities."""

import pytest
from utils import (
    segment_sentences,
    clean_claim_text,
    get_context,
    calculate_text_similarity
)


class TestEntityExtractor:
    """Test EntityExtractor class."""

    def test_extract_entities(self, entity_extractor):
        """Test entity claim_extraction."""
        text = "President Biden met with Secretary Johnson in Washington."
        entities = entity_extractor.extract(text)

        assert "President Biden" in entities or "Biden" in entities
        assert "Secretary Johnson" in entities or "Johnson" in entities
        assert "Washington" in entities

    def test_filters_stop_words(self, entity_extractor):
        """Test that stop words are filtered."""
        text = "The company announced this."
        entities = entity_extractor.extract(text)

        assert "The" not in entities
        assert "This" not in entities

    def test_empty_text(self, entity_extractor):
        """Test claim_extraction from empty text."""
        entities = entity_extractor.extract("")
        assert entities == []


class TestTemporalExtractor:
    """Test TemporalExtractor class."""

    def test_extract_dates(self, temporal_extractor):
        """Test date claim_extraction."""
        text = "The event occurred on January 15, 2024 and will continue tomorrow."
        markers = temporal_extractor.extract(text)

        assert any("January 15, 2024" in m for m in markers)
        assert any("tomorrow" in m.lower() for m in markers)

    def test_extract_relative_time(self, temporal_extractor):
        """Test relative time claim_extraction."""
        text = "This happened yesterday and will continue next month."
        markers = temporal_extractor.extract(text)

        assert any("yesterday" in m.lower() for m in markers)
        assert any("next month" in m.lower() for m in markers)

    def test_no_temporal_markers(self, temporal_extractor):
        """Test text without temporal markers."""
        text = "The economy is strong."
        markers = temporal_extractor.extract(text)

        assert markers == []


class TestNumericalExtractor:
    """Test NumericalExtractor class."""

    def test_extract_numbers(self, numerical_extractor):
        """Test numerical data claim_extraction."""
        text = "The unemployment rate is 3.5% which is very low."
        data = numerical_extractor.extract(text)

        assert len(data) >= 1
        assert any("3.5" in d["value"] or "3.5%" in d["value"] for d in data)
        assert "rate" in data[0]["context_before"]

    def test_extract_multiple_numbers(self, numerical_extractor):
        """Test claim_extraction of multiple numbers."""
        text = "Revenue was 1.2 billion, up from 800 million."
        data = numerical_extractor.extract(text)

        assert len(data) >= 2
        values = [d["value"] for d in data]
        assert any("1.2" in v for v in values)
        assert any("800" in v for v in values)

    def test_context_capture(self, numerical_extractor):
        """Test that context is properly captured."""
        text = "The population grew to 5 million people last year."
        data = numerical_extractor.extract(text)

        assert len(data) > 0
        assert data[0]["full_context"] != ""
        assert "5" in data[0]["full_context"]


class TestSegmentSentences:
    """Test sentence segmentation."""

    def test_basic_segmentation(self):
        """Test basic sentence segmentation."""
        text = "First sentence. Second sentence. Third sentence."
        sentences = segment_sentences(text)

        assert len(sentences) == 3
        assert "First sentence" in sentences[0]
        assert "Second sentence" in sentences[1]
        assert "Third sentence" in sentences[2]

    def test_abbreviations(self):
        """Test handling of abbreviations."""
        text = "Dr. Smith works here. Mr. Jones is there."
        sentences = segment_sentences(text)

        assert len(sentences) == 2
        assert "Dr. Smith" in sentences[0]
        assert "Mr. Jones" in sentences[1]

    def test_exclamation_question(self):
        """Test exclamation and question marks."""
        text = "Is this true? Yes it is! That's great."
        sentences = segment_sentences(text)

        assert len(sentences) == 3

    def test_empty_text(self):
        """Test empty text."""
        sentences = segment_sentences("")
        assert sentences == []


class TestCleanClaimText:
    """Test claim text cleaning."""

    def test_removes_extra_whitespace(self):
        """Test removal of extra whitespace."""
        text = "This  has   extra    spaces."
        cleaned = clean_claim_text(text)

        assert "  " not in cleaned
        assert cleaned == "This has extra spaces."

    def test_adds_period(self):
        """Test adding period if missing."""
        text = "This has no period"
        cleaned = clean_claim_text(text)

        assert cleaned.endswith(".")

    def test_preserves_existing_punctuation(self):
        """Test preserves existing punctuation."""
        text = "Does this work?"
        cleaned = clean_claim_text(text)

        assert cleaned == "Does this work?"

    def test_strips_whitespace(self):
        """Test stripping leading/trailing whitespace."""
        text = "  Text with spaces  "
        cleaned = clean_claim_text(text)

        assert cleaned == "Text with spaces."


class TestGetContext:
    """Test context retrieval."""

    def test_get_context_middle(self):
        """Test getting context from middle."""
        sentences = ["First.", "Second.", "Third.", "Fourth."]
        context = get_context(sentences, 1, window=1)

        assert "First" in context
        assert "Second" in context
        assert "Third" in context
        assert "Fourth" not in context

    def test_get_context_start(self):
        """Test getting context from start."""
        sentences = ["First.", "Second.", "Third."]
        context = get_context(sentences, 0, window=1)

        assert "First" in context
        assert "Second" in context
        assert "Third" not in context

    def test_get_context_end(self):
        """Test getting context from end."""
        sentences = ["First.", "Second.", "Third."]
        context = get_context(sentences, 2, window=1)

        assert "First" not in context
        assert "Second" in context
        assert "Third" in context


class TestCalculateTextSimilarity:
    """Test text similarity calculation."""

    def test_identical_texts(self):
        """Test identical texts have similarity of 1.0."""
        text = "This is a test"
        similarity = calculate_text_similarity(text, text)

        assert similarity == 1.0

    def test_completely_different(self):
        """Test completely different texts have similarity of 0.0."""
        text1 = "cat dog bird"
        text2 = "apple orange banana"
        similarity = calculate_text_similarity(text1, text2)

        assert similarity == 0.0

    def test_partial_overlap(self):
        """Test partial overlap gives intermediate similarity."""
        text1 = "the quick brown fox"
        text2 = "the lazy brown dog"
        similarity = calculate_text_similarity(text1, text2)

        assert 0.0 < similarity < 1.0
        assert abs(similarity - 0.333) < 0.01

    def test_empty_texts(self):
        """Test empty texts."""
        similarity = calculate_text_similarity("", "test")
        assert similarity == 0.0