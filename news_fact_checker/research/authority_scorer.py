"""Authority scoring for sources."""

from __future__ import annotations

from typing import List, Optional
from news_fact_checker.research.constants import (
    GOVERNMENT_MARKERS,
    REPUTABLE_NEWS_MARKERS,
    AUTHORITY_WEIGHTS,
)


class AuthorityScorer:

    def __init__(self):
        self.government_markers = GOVERNMENT_MARKERS
        self.news_markers = REPUTABLE_NEWS_MARKERS
        self.weights = AUTHORITY_WEIGHTS

    def score(self, url: str, authoritative_domains: Optional[List[str]] = None) -> float:
        if not url:
            return self.weights["default"]

        url_lower = url.lower()

        if authoritative_domains:
            if self._matches_authoritative(url_lower, authoritative_domains):
                return 1.0

        if self._is_government(url_lower):
            return self.weights["government"]

        if self._is_reputable_news(url_lower):
            return self.weights["news"]

        return self.weights["default"]

    def _matches_authoritative(self, url: str, domains: List[str]) -> bool:
        domains_lower = [d.lower() for d in domains if d]
        return any(domain in url for domain in domains_lower)

    def _is_government(self, url: str) -> bool:
        return any(marker in url for marker in self.government_markers)

    def _is_reputable_news(self, url: str) -> bool:
        return any(marker in url for marker in self.news_markers)