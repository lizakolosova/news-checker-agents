from __future__ import annotations

import re
from typing import List
import structlog

from news_fact_checker.claim_extraction.models import Claim, ClaimType
from news_fact_checker.utils import clean_claim_text
from news_fact_checker.research.models import QueryPlan
from news_fact_checker.research.constants import DEFAULT_MAX_QUERIES

logger = structlog.get_logger().bind(component="query_strategy")


class HeuristicQueryBuilder:

    def build_queries(self, claim: Claim, max_queries: int = DEFAULT_MAX_QUERIES) -> List[str]:
        base_query = clean_claim_text(claim.text)

        queries: List[str] = [base_query]

        entities = " ".join(claim.entities or [])
        if entities:
            queries.append(f'"{entities}" {base_query}')

        dates = " ".join(claim.temporal_markers or [])
        if dates:
            queries.append(f"{base_query} {dates}")

        numbers = " ".join([str(d.get("value", "")) for d in (claim.numerical_data or [])])
        if numbers:
            queries.append(f'{base_query} "{numbers}"')

        if claim.claim_type in {ClaimType.STATISTICAL, ClaimType.TEMPORAL}:
            queries.extend([
                f"{base_query} official statistics",
                f"{base_query} statistical office",
                f"{base_query} central bank statement",
                f"{base_query} government report",
            ])

        return self._deduplicate_queries(queries, max_queries)

    def _deduplicate_queries(self, queries: List[str], max_queries: int) -> List[str]:
        seen = set()
        unique: List[str] = []

        for query in queries:
            normalized = re.sub(r"\s+", " ", query).strip()
            if normalized and normalized not in seen:
                unique.append(normalized)
                seen.add(normalized)

        return unique[:max_queries]


class LLMPromptBuilder:

    def build(self, claim_text: str, claim_type: str) -> str:
        return f"""You are a research strategist for a fact-checking system.

Analyze this claim and respond with ONLY a valid JSON object (no markdown, no backticks, no explanations).

Your tasks:
1. Identify the domain: government_statistics, entertainment, sports, corporate, mixed, or other
2. Create 3-6 high-quality search queries for official/reputable sources
3. Create 1-3 broader news-style queries
4. List 3-8 authoritative domains for this claim type

Required JSON format:
{{
  "domain": "government_statistics",
  "authority_queries": ["query 1", "query 2", "query 3"],
  "news_queries": ["news query 1", "news query 2"],
  "authoritative_domains": ["domain1.com", "domain2.org"]
}}

Claim type: {claim_type}
Claim: {claim_text}

JSON response:"""


class QueryStrategy:

    def __init__(self):
        self.heuristic_builder = HeuristicQueryBuilder()
        self.prompt_builder = LLMPromptBuilder()

    def create_fallback_plan(self, claim: Claim) -> QueryPlan:
        queries = self.heuristic_builder.build_queries(claim)

        return QueryPlan(
            domain="unknown",
            authority_queries=queries,
            news_queries=queries[:2],
            authoritative_domains=[],
            strategy="deterministic_fallback",
        )

    def build_llm_prompt(self, claim_text: str, claim_type: str) -> str:
        return self.prompt_builder.build(claim_text, claim_type)