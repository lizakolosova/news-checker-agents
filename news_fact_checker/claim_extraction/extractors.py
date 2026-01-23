from __future__ import annotations

from typing import List, Dict, Any
from news_fact_checker.claim_extraction.patterns import ClaimPatterns


class EntityExtractor:

    def __init__(self, patterns: ClaimPatterns):
        self.patterns = patterns
        self.stop_words = {
            "The", "This", "That", "These", "Those", "A", "An", "And", "But", "Or",
            "In", "On", "At", "By", "From", "To", "As", "It", "Its", "Their", "They",
        }
        self.month_words = {
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        }

    def extract(self, text: str) -> List[str]:
        entities = self.patterns.entity_pattern.findall(text)

        cleaned: List[str] = []
        for e in entities:
            e = e.strip()
            if not e or e in self.stop_words:
                continue
            if e in self.month_words:
                continue
            cleaned.append(e)

        seen = set()
        out = []
        for e in cleaned:
            if e not in seen:
                out.append(e)
                seen.add(e)
        return out


class NumberExtractor:

    def __init__(self, patterns: ClaimPatterns):
        self.patterns = patterns

    def extract(self, text: str) -> List[Dict[str, Any]]:
        numbers = []
        for match in self.patterns.number_pattern.finditer(text):
            raw = match.group(0)
            numbers.append({
                "value": raw,
                "start": match.start(),
                "end": match.end(),
            })
        return numbers


class TemporalExtractor:

    def __init__(self, patterns: ClaimPatterns):
        self.patterns = patterns

    def extract(self, text: str) -> List[str]:
        markers: List[str] = []
        markers.extend(self.patterns.date_pattern.findall(text))
        markers.extend(self.patterns.temporal_marker_pattern.findall(text))
        markers.extend(self.patterns.relative_time_pattern.findall(text))

        seen = set()
        out = []
        for m in markers:
            m = " ".join(m.split()).strip()
            if m and m not in seen:
                out.append(m)
                seen.add(m)
        return out