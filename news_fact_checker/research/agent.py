"""
Hybrid LLM Research Agent (retrieval only).

Responsibilities:
- Use an LLM to detect the claim domain and suggest search queries
- Use Serper to perform web search
- Filter low-signal sources and rank by relevance
- Return raw evidence snippets for evaluation

This agent does NOT:
- Score source credibility
- Classify stance (supports / refutes / unclear)
- Compute consensus or verdicts
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from news_fact_checker.research.utils import fallback_query_plan

import structlog

from news_fact_checker import Claim
from news_fact_checker.config import ResearchConfig
from news_fact_checker.research.evidence_filter import filter_low_signal, score_and_keep
from news_fact_checker.research.parsing import parse_llm_response
from news_fact_checker.research.serper_client import SerperClient
from news_fact_checker.research.utils import authority_weight, build_llm_prompt, get_claim_type_str, fallback_query_plan
from news_fact_checker.utils import clean_claim_text

try:
    from ollama import Client as OllamaClient
except ImportError:
    OllamaClient = None

logger = structlog.get_logger().bind(component="research_agent")

LOW_SIGNAL_DOMAINS = (
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "pinterest.com",
    "reddit.com",
    "quora.com",
)

@dataclass
class ResearchAgent:
    """Agent responsible for researching claims and gathering raw evidence."""

    def __init__(
            self,
            config: Optional[ResearchConfig] = None,
            llm_client: Optional[Any] = None,
    ):
        """
        Initialize the research agent.

        Args:
            config: Research configuration (defaults from environment)
            llm_client: Optional LLM client (Groq, OpenAI, or Ollama)
        """
        self.config = config or ResearchConfig(
            search_api_key="dae9dbfe92891624116876b484dbbfcccb52ddbe",
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
        )

        self.logger = structlog.get_logger().bind(component="research_agent")
        self.serper = SerperClient(api_key=self.config.search_api_key)

        if llm_client is not None:
            self.llm_client = llm_client
        elif OllamaClient is not None:
            self.llm_client = OllamaClient()
        else:
            self.llm_client = None

        if not self.llm_client:
            self.logger.warning(
                "llm_disabled",
                reason="No LLM client available - using heuristic query planning",
            )

    def research_claims(self, claims: List[Claim]) -> List[Dict[str, Any]]:
        """
        Research multiple claims and gather evidence.

        Returns list of dicts with:
            - claim_id: Unique identifier
            - original_claim: Original claim text
            - claim_type: Type of claim
            - evidence: List of evidence items with URLs, snippets, relevance scores
            - metadata: Research quality metrics and timing
        """
        if not claims:
            self.logger.warning("research_claims_empty", msg="No claims provided")
            return []

        results: List[Dict[str, Any]] = []

        for claim in claims:
            trace_id = str(uuid.uuid4())
            start_time = time.time()

            self.logger.info(
                "research_started",
                trace_id=trace_id,
                claim_id=claim.claim_id,
                claim_preview=claim.text[:80],
            )

            try:
                query_plan = self._generate_query_plan(claim, trace_id)

                evidence = self._progressive_retrieval(claim, query_plan, trace_id)

                quality_report = self._assess_quality(evidence, trace_id)

                duration_ms = (time.time() - start_time) * 1000.0

                results.append({
                    "claim_id": claim.claim_id,
                    "original_claim": claim.text,
                    "claim_type": (
                        claim.claim_type.value
                        if hasattr(claim, "claim_type")
                        else None
                    ),
                    "evidence": evidence,
                    "metadata": {
                        "duration_ms": round(duration_ms, 2),
                        "quality_score": quality_report["quality_score"],
                        "tier1_sources": quality_report["tier1_count"],
                        "detected_domain": query_plan.get("domain", "unknown"),
                        "strategy_used": quality_report["strategy_used"],
                    },
                })

                self.logger.info(
                    "research_finished",
                    trace_id=trace_id,
                    claim_id=claim.claim_id,
                    evidence_count=len(evidence),
                    quality_score=quality_report["quality_score"],
                )

            except Exception as e:
                self.logger.error(
                    "research_failed",
                    trace_id=trace_id,
                    claim_id=claim.claim_id,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                results.append({
                    "claim_id": claim.claim_id,
                    "original_claim": claim.text,
                    "claim_type": None,
                    "evidence": [],
                    "metadata": {
                        "duration_ms": 0,
                        "quality_score": 0.0,
                        "tier1_sources": 0,
                        "detected_domain": "error",
                        "strategy_used": "failed",
                        "error": str(e),
                    },
                })

        return results

    def _generate_query_plan(self, claim: Claim, trace_id: str) -> Dict[str, Any]:
        """Generate search query plan using LLM or fallback to heuristics."""
        if not self.llm_client:
            return fallback_query_plan(claim)

        claim_text = clean_claim_text(claim.text)
        claim_type = get_claim_type_str(claim)
        prompt = build_llm_prompt(claim_text, claim_type)

        try:
            content = self._call_llm_for_query_plan(prompt)
            return parse_llm_response(content, claim, trace_id)
        except Exception as e:
            self.logger.warning(
                "llm_query_plan_failed",
                trace_id=trace_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return fallback_query_plan(claim)

    def _call_llm_for_query_plan(self, prompt: str) -> str:
        """
        Call LLM client and return text content.

        Supports:
        - Groq/OpenAI-style: client.chat.completions.create(...)
        - Ollama: client.chat(model=..., messages=[...])
        """
        if not self.llm_client:
            raise RuntimeError("LLM client not configured")

        chat_attr = getattr(self.llm_client, "chat", None)
        if chat_attr is not None and hasattr(chat_attr, "completions"):
            resp = self.llm_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            return resp.choices[0].message.content

        if hasattr(self.llm_client, "chat"):
            resp = self.llm_client.chat(
                model="llama3",
                messages=[{"role": "user", "content": prompt}],
            )
            msg = resp.get("message") or {}
            content = msg.get("content", "")
            if not content:
                raise ValueError("Empty content from Ollama")
            return content

        raise TypeError(f"Unsupported LLM client type: {type(self.llm_client)}")

    def _progressive_retrieval(
            self,
            claim: Claim,
            query_plan: Dict[str, Any],
            trace_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Progressive evidence retrieval strategy.

        Round 1: Authority-focused queries (with site: operators)
        Round 2: Broader news queries if needed
        """
        min_evidence = getattr(self.config, "min_evidence", 3)
        max_results = getattr(self.config, "max_evidence", 10)

        authoritative_domains = query_plan.get("authoritative_domains") or []
        authority_queries = query_plan.get("authority_queries") or []

        expanded_queries = []
        for query in authority_queries:
            query = query.strip()
            if not query:
                continue

            expanded_queries.append(query)

            for domain in authoritative_domains:
                domain = domain.strip()
                if domain:
                    expanded_queries.append(f"site:{domain} {query}")

        evidence = []
        if expanded_queries:
            evidence = self._search_and_filter(
                queries=expanded_queries,
                claim=claim,
                min_relevance=0.35,
                max_results=max_results,
                trace_id=trace_id,
                authoritative_domains=authoritative_domains,
            )

        if len(evidence) < min_evidence:
            news_queries = query_plan.get("news_queries") or []
            if news_queries:
                additional = self._search_and_filter(
                    queries=news_queries,
                    claim=claim,
                    min_relevance=0.30,
                    max_results=max_results,
                    trace_id=trace_id,
                    authoritative_domains=authoritative_domains,
                )

                evidence_by_url = {
                    e["source_url"]: e
                    for e in evidence
                    if e.get("source_url")
                }

                for ev in additional:
                    url = ev.get("source_url")
                    if not url:
                        continue

                    existing = evidence_by_url.get(url)
                    if not existing or ev["relevance_score"] > existing["relevance_score"]:
                        evidence_by_url[url] = ev

                evidence = list(evidence_by_url.values())

        return evidence

    def _search_and_filter(
            self,
            queries: List[str],
            claim: Claim,
            min_relevance: float,
            max_results: int,
            trace_id: str,
            authoritative_domains: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute web search and return ranked evidence."""
        if not queries:
            return []

        sources = self.serper.search(queries, per_query_results=3)
        if not sources:
            self.logger.warning(
                "search_returned_empty",
                trace_id=trace_id,
                query_count=len(queries),
            )
            return []

        filtered = filter_low_signal(sources, LOW_SIGNAL_DOMAINS)

        preliminary = score_and_keep(
            claim,
            filtered,
            min_relevance=min_relevance,
            keep_top_k_if_all_filtered=max_results * 2,
        )

        if not preliminary:
            return []

        evidence = []
        for source in preliminary:
            url = source.get("source_url") or source.get("url") or ""
            title = source.get("source_title") or source.get("title") or ""
            snippet = source.get("snippet") or ""

            base_relevance = float(source.get("relevance_score", 0.0))
            auth_weight = authority_weight(url, authoritative_domains)

            combined_score = 0.7 * base_relevance + 0.3 * auth_weight

            evidence.append({
                "source_url": url,
                "source_title": title,
                "snippet": snippet,
                "relevance_score": combined_score,
                "base_relevance": base_relevance,
                "authority_weight": auth_weight,
                "raw_source": source,
            })

        evidence.sort(key=lambda e: e["relevance_score"], reverse=True)

        seen_urls = set()
        unique_evidence = []
        for ev in evidence:
            url = ev.get("source_url", "")
            if url and url not in seen_urls:
                unique_evidence.append(ev)
                seen_urls.add(url)

        final = unique_evidence[:max_results]

        self.logger.info(
            "search_completed",
            trace_id=trace_id,
            queries_executed=len(queries),
            raw_results=len(sources),
            after_filter=len(filtered),
            final_evidence=len(final),
        )

        return final

    def _assess_quality(
            self,
            evidence: List[Dict[str, Any]],
            trace_id: str,
    ) -> Dict[str, Any]:
        """
        Assess retrieval quality (not evidence credibility).

        This measures how good the search was, not whether evidence
        supports/refutes the claim (handled by evaluation agent).
        """
        if not evidence:
            return {
                "quality_score": 0.0,
                "tier1_count": 0,
                "strategy_used": "no_evidence",
            }

        count = len(evidence)
        avg_relevance = sum(e.get("relevance_score", 0.0) for e in evidence) / count
        size_score = min(count / 5.0, 1.0)

        quality = 0.6 * avg_relevance + 0.4 * size_score
        quality = max(0.0, min(quality, 1.0))

        tier1_count = sum(
            1 for e in evidence
            if e.get("authority_weight", 0.0) >= 0.9
        )

        strategy = "llm_hybrid" if self.llm_client else "deterministic"

        self.logger.info(
            "retrieval_quality_assessed",
            trace_id=trace_id,
            quality_score=round(quality, 3),
            evidence_count=count,
            tier1_sources=tier1_count,
            avg_relevance=round(avg_relevance, 3),
            strategy=strategy,
        )

        return {
            "quality_score": round(quality, 3),
            "tier1_count": tier1_count,
            "strategy_used": strategy,
        }