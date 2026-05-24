from __future__ import annotations

from dataclasses import dataclass

from news_fact_checker.research.constants import (
    DEFAULT_MIN_EVIDENCE,
    DEFAULT_MAX_EVIDENCE,
    DEFAULT_PER_QUERY_RESULTS,
    DEFAULT_MAX_QUERIES,
    SEARCH_TIMEOUT_SECONDS,
)


@dataclass
class ResearchConfig:
    search_api_key: str

    min_evidence: int = DEFAULT_MIN_EVIDENCE
    max_evidence: int = DEFAULT_MAX_EVIDENCE
    per_query_results: int = DEFAULT_PER_QUERY_RESULTS
    max_queries: int = DEFAULT_MAX_QUERIES

    search_timeout: int = SEARCH_TIMEOUT_SECONDS

    enable_llm_planning: bool = True
    llm_model: str = "llama3"
    llm_temperature: float = 0.1

    def __post_init__(self):
        self._validate()

    def _validate(self):
        if not self.search_api_key:
            raise ValueError("search_api_key is required")

        if self.min_evidence < 1:
            raise ValueError(f"min_evidence must be >= 1, got {self.min_evidence}")

        if self.max_evidence < self.min_evidence:
            raise ValueError(
                f"max_evidence ({self.max_evidence}) must be >= min_evidence ({self.min_evidence})"
            )

        if self.per_query_results < 1:
            raise ValueError(f"per_query_results must be >= 1, got {self.per_query_results}")

        if self.max_queries < 1:
            raise ValueError(f"max_queries must be >= 1, got {self.max_queries}")

        if not 0 <= self.llm_temperature <= 2:
            raise ValueError(f"llm_temperature must be in [0, 2], got {self.llm_temperature}")