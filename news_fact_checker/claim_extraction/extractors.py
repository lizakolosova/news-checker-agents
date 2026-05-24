from __future__ import annotations

from typing import List, Dict, Any

from news_fact_checker.claim_extraction import patterns
from news_fact_checker.claim_extraction.constants import ENTITY_STOP_WORDS, MONTH_NAMES
from news_fact_checker.exceptions import EntityExtractionError


class EntityExtractor:

    def __init__(self, stop_words: frozenset = None, month_words: frozenset = None):
        self.stop_words = frozenset(stop_words or ENTITY_STOP_WORDS)
        self.month_words = frozenset(month_words or MONTH_NAMES)

    def extract(self, text: str) -> List[str]:
        try:
            entities = patterns.ENTITY_PATTERN.findall(text)

            cleaned: List[str] = []
            seen = set()

            for entity in entities:
                entity = entity.strip()

                if not entity or entity in self.stop_words or entity in self.month_words:
                    continue

                if entity not in seen:
                    cleaned.append(entity)
                    seen.add(entity)

            return cleaned

        except Exception as e:
            raise EntityExtractionError(f"Failed to extract entities: {e}") from e


def extract(text: str) -> List[Dict[str, Any]]:

    numbers = []
    for match in patterns.NUMBER_PATTERN.finditer(text):
        numbers.append({
            "value": match.group(0),
            "start": match.start(),
            "end": match.end(),
        })
    return numbers


class NumberExtractor:
    pass


def extract(text: str) -> List[str]:
    markers: List[str] = []

    markers.extend(patterns.DATE_PATTERN.findall(text))
    markers.extend(patterns.TEMPORAL_MARKER_PATTERN.findall(text))
    markers.extend(patterns.RELATIVE_TIME_PATTERN.findall(text))

    seen = set()
    unique_markers = []

    for marker in markers:
        marker = " ".join(marker.split()).strip()

        if marker and marker not in seen:
            unique_markers.append(marker)
            seen.add(marker)

    return unique_markers


class TemporalExtractor:
    pass


def extract_numbers(text: str) -> List[Dict[str, Any]]:
    return extract(text)


def extract_temporal(text: str) -> List[str]:
    return extract(text)


class FeatureExtractor:

    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.number_extractor = NumberExtractor()
        self.temporal_extractor = TemporalExtractor()

    def extract_all(self, text: str) -> Dict[str, Any]:
        return {
            "entities": self.entity_extractor.extract(text),
            "numerical_data": extract(text),
            "temporal_markers": extract(text),
        }

    def extract_entities(self, text: str) -> List[str]:
        return self.entity_extractor.extract(text)

