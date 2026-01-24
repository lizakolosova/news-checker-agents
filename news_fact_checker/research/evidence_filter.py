from __future__ import annotations

from typing import List, Tuple, Optional
import structlog

from news_fact_checker.claim_extraction.models import Claim
from news_fact_checker.research.models import SearchResult, EvidenceItem
from news_fact_checker.research.constants import (
    LOW_SIGNAL_DOMAINS,
    SNIPPET_MAX_LENGTH,
)
from news_fact_checker.utils import calculate_text_similarity

logger = structlog.get_logger().bind(component="evidence_filter")


class DomainFilter:

    def __init__(self, low_signal_domains: Tuple[str, ...] = LOW_SIGNAL_DOMAINS):
        self.low_signal_domains = low_signal_domains

    def filter(self, results: List[SearchResult]) -> List[SearchResult]:
        filtered = []
        for result in results:
            url = result.get("url", "") or ""
            if url and not self._is_low_signal(url):
                filtered.append(result)
        return filtered

    def _is_low_signal(self, url: str) -> bool:
        return any(domain in url for domain in self.low_signal_domains)


class RelevanceScorer:

    def score(self, claim: Claim, results: List[SearchResult]) -> List[EvidenceItem]:
        scored: List[EvidenceItem] = []

        for result in results:
            snippet = (result.get("snippet") or "").strip()
            title = (result.get("title") or "").strip()
            text = snippet or title

            if not text:
                continue

            relevance = calculate_text_similarity(claim.text, text)

            scored.append(EvidenceItem(
                source_url=result.get("url", ""),
                source_title=result.get("title", ""),
                snippet=(snippet or title)[:SNIPPET_MAX_LENGTH],
                relevance_score=round(relevance, 3),
                base_relevance=relevance,
                authority_weight=0.0,
            ))

        return scored

    def filter_by_relevance(
            self,
            scored: List[EvidenceItem],
            min_relevance: float,
            keep_top_k: int,
    ) -> List[EvidenceItem]:
        kept = [item for item in scored if item["base_relevance"] >= min_relevance]

        if not kept and scored:
            sorted_items = sorted(scored, key=lambda x: x["base_relevance"], reverse=True)
            kept = sorted_items[:keep_top_k]

        return kept


class EvidenceFilter:

    def __init__(self):
        self.domain_filter = DomainFilter()
        self.relevance_scorer = RelevanceScorer()

    def filter_and_score(
            self,
            claim: Claim,
            results: List[SearchResult],
            min_relevance: float,
            keep_top_k: int,
    ) -> List[EvidenceItem]:
        filtered = self.domain_filter.filter(results)

        if not filtered:
            logger.warning("all_results_filtered", total=len(results))
            return []

        scored = self.relevance_scorer.score(claim, filtered)

        kept = self.relevance_scorer.filter_by_relevance(scored, min_relevance, keep_top_k)

        return kept