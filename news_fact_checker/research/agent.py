from __future__ import annotations

import os
import time
import uuid
from typing import List, Optional, Any
import structlog

from news_fact_checker.claim_extraction.models import Claim
from news_fact_checker.research.config import ResearchConfig
from news_fact_checker.research.models import (
    QueryPlan,
    EvidenceItem,
    ResearchResult,
    ResearchMetrics,
    SearchMetrics,
)
from news_fact_checker.research.search_client import SearchClient
from news_fact_checker.research.llm_client import create_llm_client, LLMClient
from news_fact_checker.research.query_planner import QueryStrategy
from news_fact_checker.research.plan_parser import QueryPlanParser
from news_fact_checker.research.evidence_filter import EvidenceFilter
from news_fact_checker.research.authority_scorer import AuthorityScorer
from news_fact_checker.research.quality_assessor import QualityAssessor
from news_fact_checker.research.constants import (
    MIN_RELEVANCE_AUTHORITY,
    MIN_RELEVANCE_NEWS,
    AUTHORITY_RELEVANCE_WEIGHT,
    AUTHORITY_WEIGHT_CONTRIBUTION,
)
from news_fact_checker.utils import clean_claim_text

logger = structlog.get_logger().bind(component="research_agent")

try:
    from ollama import Client as OllamaClient
except ImportError:
    OllamaClient = None


class QueryPlanGenerator:

    def __init__(
            self,
            llm_client: Optional[LLMClient],
            query_strategy: QueryStrategy,
            plan_parser: QueryPlanParser,
    ):
        self.llm_client = llm_client
        self.query_strategy = query_strategy
        self.plan_parser = plan_parser

    def generate(self, claim: Claim, trace_id: str) -> QueryPlan:
        if not self.llm_client:
            return self.query_strategy.create_fallback_plan(claim)

        try:
            claim_text = clean_claim_text(claim.text)
            claim_type = self._get_claim_type_str(claim)

            prompt = self.query_strategy.build_llm_prompt(claim_text, claim_type)
            content = self.llm_client.generate(prompt)

            return self.plan_parser.parse(content, claim, trace_id)

        except Exception as e:
            logger.warning(
                "llm_query_plan_failed",
                trace_id=trace_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return self.query_strategy.create_fallback_plan(claim)

    def _get_claim_type_str(self, claim: Claim) -> str:
        claim_type = getattr(claim, "claim_type", None)
        if hasattr(claim_type, "value"):
            return claim_type.value
        return str(claim_type) if claim_type else "unknown"


class EvidenceRetriever:

    def __init__(
            self,
            search_client: SearchClient,
            evidence_filter: EvidenceFilter,
            authority_scorer: AuthorityScorer,
            config: ResearchConfig,
    ):
        self.search_client = search_client
        self.evidence_filter = evidence_filter
        self.authority_scorer = authority_scorer
        self.config = config

    def retrieve(
            self,
            claim: Claim,
            query_plan: QueryPlan,
            trace_id: str,
    ) -> List[EvidenceItem]:
        metrics = SearchMetrics()

        authoritative_domains = query_plan.get("authoritative_domains") or []
        evidence = self._search_authority(
            claim, query_plan, authoritative_domains, trace_id, metrics
        )

        if len(evidence) < self.config.min_evidence:
            additional = self._search_news(
                claim, query_plan, authoritative_domains, trace_id, metrics
            )
            evidence = self._merge_evidence(evidence, additional)

        logger.info("search_completed", trace_id=trace_id, **metrics.to_dict())

        return evidence

    def _search_authority(
            self,
            claim: Claim,
            query_plan: QueryPlan,
            authoritative_domains: List[str],
            trace_id: str,
            metrics: SearchMetrics,
    ) -> List[EvidenceItem]:
        authority_queries = query_plan.get("authority_queries") or []
        expanded_queries = self._expand_queries(authority_queries, authoritative_domains)

        if not expanded_queries:
            return []

        return self._execute_search(
            claim,
            expanded_queries,
            MIN_RELEVANCE_AUTHORITY,
            authoritative_domains,
            trace_id,
            metrics,
        )

    def _search_news(
            self,
            claim: Claim,
            query_plan: QueryPlan,
            authoritative_domains: List[str],
            trace_id: str,
            metrics: SearchMetrics,
    ) -> List[EvidenceItem]:
        news_queries = query_plan.get("news_queries") or []

        if not news_queries:
            return []

        return self._execute_search(
            claim,
            news_queries,
            MIN_RELEVANCE_NEWS,
            authoritative_domains,
            trace_id,
            metrics,
        )

    def _expand_queries(
            self,
            queries: List[str],
            domains: List[str],
    ) -> List[str]:
        expanded = []

        for query in queries:
            query = query.strip()
            if not query:
                continue

            expanded.append(query)

            for domain in domains:
                domain = domain.strip()
                if domain:
                    expanded.append(f"site:{domain} {query}")

        return expanded

    def _execute_search(
            self,
            claim: Claim,
            queries: List[str],
            min_relevance: float,
            authoritative_domains: List[str],
            trace_id: str,
            metrics: SearchMetrics,
    ) -> List[EvidenceItem]:
        if not queries:
            return []

        results = self.search_client.search(queries, self.config.per_query_results)
        metrics.raw_results += len(results)
        metrics.queries_executed += len(queries)

        if not results:
            logger.warning(
                "search_returned_empty",
                trace_id=trace_id,
                query_count=len(queries),
            )
            return []

        scored = self.evidence_filter.filter_and_score(
            claim,
            results,
            min_relevance,
            self.config.max_evidence * 2,
        )
        metrics.after_filter += len(scored)

        evidence = self._apply_authority_scores(scored, authoritative_domains)
        evidence.sort(key=lambda e: e["relevance_score"], reverse=True)

        final = self._deduplicate(evidence)[:self.config.max_evidence]
        metrics.final_evidence = len(final)

        return final

    def _apply_authority_scores(
            self,
            items: List[EvidenceItem],
            authoritative_domains: List[str],
    ) -> List[EvidenceItem]:
        for item in items:
            url = item.get("source_url", "")
            base_relevance = item.get("base_relevance", 0.0)

            authority_weight = self.authority_scorer.score(url, authoritative_domains)

            combined_score = (
                    AUTHORITY_RELEVANCE_WEIGHT * base_relevance +
                    AUTHORITY_WEIGHT_CONTRIBUTION * authority_weight
            )

            item["relevance_score"] = combined_score
            item["authority_weight"] = authority_weight

        return items

    def _merge_evidence(
            self,
            primary: List[EvidenceItem],
            additional: List[EvidenceItem],
    ) -> List[EvidenceItem]:
        evidence_by_url = {
            e["source_url"]: e
            for e in primary
            if e.get("source_url")
        }

        for item in additional:
            url = item.get("source_url")
            if not url:
                continue

            existing = evidence_by_url.get(url)
            if not existing or item["relevance_score"] > existing["relevance_score"]:
                evidence_by_url[url] = item

        return list(evidence_by_url.values())

    def _deduplicate(self, evidence: List[EvidenceItem]) -> List[EvidenceItem]:
        seen_urls = set()
        unique = []

        for item in evidence:
            url = item.get("source_url", "")
            if url and url not in seen_urls:
                unique.append(item)
                seen_urls.add(url)

        return unique


class ResearchAgent:

    def __init__(
            self,
            config: Optional[ResearchConfig] = None,
            llm_client: Optional[Any] = None,
    ):
        self.config = config or ResearchConfig(
            search_api_key=os.getenv("SERPER_API_KEY", ""),
        )

        self.search_client = SearchClient(
            self.config.search_api_key,
            self.config.search_timeout,
        )

        if llm_client is not None:
            self.llm_client = create_llm_client(llm_client, self.config.llm_temperature)
        elif self.config.enable_llm_planning and OllamaClient is not None:
            self.llm_client = create_llm_client(OllamaClient(), self.config.llm_temperature)
        else:
            self.llm_client = None

        if not self.llm_client:
            logger.warning(
                "llm_disabled",
                reason="No LLM client available - using heuristic query planning",
            )

        self.query_plan_generator = QueryPlanGenerator(
            self.llm_client,
            QueryStrategy(),
            QueryPlanParser(),
        )

        self.evidence_retriever = EvidenceRetriever(
            self.search_client,
            EvidenceFilter(),
            AuthorityScorer(),
            self.config,
        )

        self.quality_assessor = QualityAssessor()

    def research(self, claims: List[Claim]) -> List[ResearchResult]:
        if not claims:
            logger.warning("research_claims_empty")
            return []

        results: List[ResearchResult] = []

        for claim in claims:
            result = self._research_claim(claim)
            results.append(result)

        return results

    def research_claims(self, claims: List[Claim]) -> List[ResearchResult]:
        return self.research(claims)

    def _research_claim(self, claim: Claim) -> ResearchResult:
        trace_id = str(uuid.uuid4())
        start_time = time.time()

        logger.info(
            "research_started",
            trace_id=trace_id,
            claim_id=claim.claim_id,
            claim_preview=claim.text[:80],
        )

        try:
            query_plan = self.query_plan_generator.generate(claim, trace_id)
            evidence = self.evidence_retriever.retrieve(claim, query_plan, trace_id)
            quality_report = self.quality_assessor.assess(
                evidence,
                self.llm_client is not None,
                trace_id,
            )

            duration_ms = (time.time() - start_time) * 1000.0

            metrics = ResearchMetrics(
                duration_ms=duration_ms,
                quality_score=quality_report["quality_score"],
                tier1_sources=quality_report["tier1_count"],
                detected_domain=query_plan.get("domain", "unknown"),
                strategy_used=quality_report["strategy_used"],
            )

            logger.info(
                "research_finished",
                trace_id=trace_id,
                claim_id=claim.claim_id,
                evidence_count=len(evidence),
                quality_score=quality_report["quality_score"],
            )

            return self._create_result(claim, evidence, metrics)

        except Exception as e:
            logger.error(
                "research_failed",
                trace_id=trace_id,
                claim_id=claim.claim_id,
                error=str(e),
                error_type=type(e).__name__,
            )

            duration_ms = (time.time() - start_time) * 1000.0
            metrics = ResearchMetrics(
                duration_ms=duration_ms,
                quality_score=0.0,
                tier1_sources=0,
                detected_domain="error",
                strategy_used="failed",
                error=str(e),
            )

            return self._create_result(claim, [], metrics)

    def _create_result(
            self,
            claim: Claim,
            evidence: List[EvidenceItem],
            metrics: ResearchMetrics,
    ) -> ResearchResult:
        claim_type = getattr(claim, "claim_type", None)
        claim_type_str = claim_type.value if hasattr(claim_type, "value") else None

        return ResearchResult(
            claim_id=claim.claim_id,
            original_claim=claim.text,
            claim_type=claim_type_str,
            evidence=evidence,
            metadata=metrics.to_dict(),
        )