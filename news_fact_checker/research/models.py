from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict


class SearchResult(TypedDict, total=False):
    url: str
    title: str
    snippet: str
    kind: str


class EvidenceItem(TypedDict, total=False):
    source_url: str
    source_title: str
    snippet: str
    published_date: Optional[str]
    claim_id: str
    relevance_score: float
    base_relevance: float
    authority_weight: float
    raw_source: Dict[str, Any]


class QueryPlan(TypedDict):
    domain: str
    authority_queries: List[str]
    news_queries: List[str]
    authoritative_domains: List[str]
    strategy: str


class ResearchResult(TypedDict):
    claim_id: str
    original_claim: str
    claim_type: Optional[str]
    evidence: List[EvidenceItem]
    metadata: Dict[str, Any]


class QualityReport(TypedDict):
    quality_score: float
    tier1_count: int
    strategy_used: str


@dataclass
class SearchMetrics:
    queries_executed: int = 0
    raw_results: int = 0
    after_filter: int = 0
    final_evidence: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "queries_executed": self.queries_executed,
            "raw_results": self.raw_results,
            "after_filter": self.after_filter,
            "final_evidence": self.final_evidence,
        }


@dataclass
class ResearchMetrics:
    duration_ms: float
    quality_score: float
    tier1_sources: int
    detected_domain: str
    strategy_used: str
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "duration_ms": round(self.duration_ms, 2),
            "quality_score": self.quality_score,
            "tier1_sources": self.tier1_sources,
            "detected_domain": self.detected_domain,
            "strategy_used": self.strategy_used,
        }
        if self.error:
            data["error"] = self.error
        return data