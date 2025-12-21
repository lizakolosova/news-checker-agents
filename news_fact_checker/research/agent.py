# news_fact_checker/research/agent.py
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

import json
import os
import re
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import structlog

from news_fact_checker import Claim
from news_fact_checker.claim_extraction.models import ClaimType
from news_fact_checker.config import ResearchConfig
from news_fact_checker.research.evidence_filter import filter_low_signal, score_and_keep
from news_fact_checker.research.query_builder import generate_queries
from news_fact_checker.research.serper_client import SerperClient
from news_fact_checker.utils import clean_claim_text

try:
    from ollama import Client as OllamaClient
except ImportError:
    OllamaClient = None

logger = structlog.get_logger().bind(component="research_agent")

# Domains to exclude from evidence gathering
LOW_SIGNAL_DOMAINS = (
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "pinterest.com",
    "reddit.com",
    "quora.com",
)


def _authority_weight(url: str, authoritative_domains: Optional[List[str]] = None) -> float:
    """Calculate authority weight [0, 1] based on URL domain."""
    if not url:
        return 0.0

    url_lower = url.lower()

    # Check LLM-suggested authoritative domains
    if authoritative_domains:
        auth_lower = [d.lower() for d in authoritative_domains if d]
        if any(domain in url_lower for domain in auth_lower):
            return 1.0

    # Government and international organizations
    gov_markers = (".gov", ".gouv", ".gov.uk", ".gv.", ".stat.", "europa.eu", ".int")
    if any(marker in url_lower for marker in gov_markers):
        return 0.9

    # Mainstream news sources
    news_markers = (
        "reuters.com", "apnews.com", "bbc.com", "nytimes.com",
        "ft.com", "bloomberg.com", "wsj.com", "theguardian.com",
    )
    if any(marker in url_lower for marker in news_markers):
        return 0.6

    return 0.0


def _fallback_query_plan(claim: Claim) -> Dict[str, Any]:
    """Generate fallback query plan when LLM is unavailable."""
    base_queries = generate_queries(claim, max_queries=5)
    return {
        "domain": "unknown",
        "authority_queries": base_queries,
        "news_queries": base_queries[:2],
        "authoritative_domains": [],
        "strategy": "deterministic_fallback",
    }


def _build_llm_prompt(claim_text: str, claim_type: str) -> str:
    """Build prompt for LLM query generation with strict JSON formatting."""
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


def _get_claim_type_str(claim: Claim) -> str:
    """Extract claim type as string."""
    claim_type = getattr(claim, "claim_type", None)
    if isinstance(claim_type, ClaimType):
        return claim_type.value
    return str(claim_type) if claim_type else "unknown"


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

        # LLM client setup for query planning
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
                # Generate query plan using LLM or fallback
                query_plan = self._generate_query_plan(claim, trace_id)

                # Retrieve evidence from web
                evidence = self._progressive_retrieval(claim, query_plan, trace_id)

                # Assess retrieval quality
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

    # ================================================================
    # QUERY PLANNING
    # ================================================================

    def _generate_query_plan(self, claim: Claim, trace_id: str) -> Dict[str, Any]:
        """Generate search query plan using LLM or fallback to heuristics."""
        if not self.llm_client:
            return _fallback_query_plan(claim)

        claim_text = clean_claim_text(claim.text)
        claim_type = _get_claim_type_str(claim)
        prompt = _build_llm_prompt(claim_text, claim_type)

        try:
            content = self._call_llm_for_query_plan(prompt)
            return self._parse_llm_response(content, claim, trace_id)
        except Exception as e:
            self.logger.warning(
                "llm_query_plan_failed",
                trace_id=trace_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return _fallback_query_plan(claim)

    def _call_llm_for_query_plan(self, prompt: str) -> str:
        """
        Call LLM client and return text content.

        Supports:
        - Groq/OpenAI-style: client.chat.completions.create(...)
        - Ollama: client.chat(model=..., messages=[...])
        """
        if not self.llm_client:
            raise RuntimeError("LLM client not configured")

        # Try Groq/OpenAI style
        chat_attr = getattr(self.llm_client, "chat", None)
        if chat_attr is not None and hasattr(chat_attr, "completions"):
            resp = self.llm_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            return resp.choices[0].message.content

        # Try Ollama style
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

    def _parse_llm_response(
            self,
            content: str,
            claim: Claim,
            trace_id: str,
    ) -> Dict[str, Any]:
        """
        Parse and validate LLM response into query plan.

        Handles:
        - Extra text before/after JSON
        - Markdown code blocks
        - Malformed JSON with missing braces
        - Python tuple syntax in lists
        """
        plan: Dict[str, Any] = {
            "domain": "unknown",
            "authority_queries": [],
            "news_queries": [],
            "authoritative_domains": [],
            "strategy": "llm",
        }

        raw = (content or "").strip()

        try:
            # Remove markdown code blocks if present
            raw = re.sub(r'```(?:json)?\s*', '', raw)
            raw = re.sub(r'```\s*$', '', raw)

            # Find JSON object boundaries
            start = raw.find("{")
            if start == -1:
                raise ValueError("No '{' found in LLM response")

            candidate = raw[start:]

            # Fix Python tuple syntax: ("text") -> "text"
            # This handles the malformed output from your LLM
            candidate = re.sub(r'\(\s*"([^"]+)"\s*\)', r'"\1"', candidate)

            # Try to parse JSON
            try:
                plan_json = json.loads(candidate)
            except json.JSONDecodeError:
                # Auto-close braces if needed
                open_braces = candidate.count("{")
                close_braces = candidate.count("}")
                if close_braces < open_braces:
                    candidate += "}" * (open_braces - close_braces)

                # Try parsing again
                plan_json = json.loads(candidate)

            # Extract and validate fields
            for key in ("domain", "authority_queries", "news_queries", "authoritative_domains"):
                if key in plan_json:
                    value = plan_json[key]

                    # Ensure lists are actually lists
                    if key.endswith("_queries") or key == "authoritative_domains":
                        if not isinstance(value, list):
                            value = [value] if value else []
                        # Clean up any remaining tuple artifacts
                        value = [
                            str(item).strip('()"\' ')
                            for item in value
                            if item
                        ]

                    plan[key] = value

            self.logger.info(
                "llm_query_plan_success",
                trace_id=trace_id,
                domain=plan["domain"],
                authority_count=len(plan["authority_queries"]),
                news_count=len(plan["news_queries"]),
            )

        except Exception as e:
            self.logger.warning(
                "llm_query_plan_parse_failed",
                trace_id=trace_id,
                raw_preview=raw[:400],
                error=str(e),
                error_type=type(e).__name__,
            )
            return _fallback_query_plan(claim)

        return plan

    # ================================================================
    # EVIDENCE RETRIEVAL
    # ================================================================

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

        # Expand authority queries with site: operators
        expanded_queries = []
        for query in authority_queries:
            query = query.strip()
            if not query:
                continue

            expanded_queries.append(query)

            # Add site-specific versions
            for domain in authoritative_domains:
                domain = domain.strip()
                if domain:
                    expanded_queries.append(f"site:{domain} {query}")

        # Round 1: Authority search
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

        # Round 2: News search if needed
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
            auth_weight = _authority_weight(url, authoritative_domains)

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