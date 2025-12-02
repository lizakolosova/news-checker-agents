"""Extraction utilities for entities, numbers, and temporal markers."""

from typing import List, Dict, Any
from patterns import ClaimPatterns


class EntityExtractor:
    """Extracts named entities from text."""

    def __init__(self, patterns: ClaimPatterns):
        """
        Initialize entity extractor.

        Args:
            patterns: ClaimPatterns instance
        """
        self.patterns = patterns
        self.stop_words = {'The', 'This', 'That', 'These', 'Those', 'A', 'An'}

    def extract(self, text: str) -> List[str]:
        """
        Extract named entities from text.

        Args:
            text: Input text

        Returns:
            List of entity strings
        """
        entities = self.patterns.entity_pattern.findall(text)
        entities = [e for e in entities if e not in self.stop_words]
        return list(set(entities))


class TemporalExtractor:
    """Extracts temporal markers from text."""

    def __init__(self, patterns: ClaimPatterns):
        """
        Initialize temporal extractor.

        Args:
            patterns: ClaimPatterns instance
        """
        self.patterns = patterns

    def extract(self, text: str) -> List[str]:
        """
        Extract temporal markers (dates, times) from text.

        Args:
            text: Input text

        Returns:
            List of temporal markers
        """
        markers = self.patterns.date_pattern.findall(text)
        relative_time = self.patterns.relative_time_pattern.findall(text)
        markers.extend(relative_time)
        return markers


class NumericalExtractor:
    """Extracts numerical data with context."""

    def __init__(self, patterns: ClaimPatterns):
        """
        Initialize numerical extractor.

        Args:
            patterns: ClaimPatterns instance
        """
        self.patterns = patterns
        self.context_words = 5

    def extract(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract numerical data with context.

        Args:
            text: Input text

        Returns:
            List of dictionaries containing numerical data
        """
        numerical_data = []

        for match in self.patterns.number_pattern.finditer(text):
            value = match.group()
            start_pos = match.start()

            # Get context around the number
            words_before = text[:start_pos].split()
            context_before = ' '.join(
                words_before[-self.context_words:]
                if len(words_before) >= self.context_words
                else words_before
            )

            words_after = text[match.end():].split()
            context_after = ' '.join(
                words_after[:self.context_words]
                if len(words_after) >= self.context_words
                else words_after
            )

            numerical_data.append({
                'value': value,
                'context_before': context_before,
                'context_after': context_after,
                'full_context': f"{context_before} {value} {context_after}"
            })

        return numerical_data