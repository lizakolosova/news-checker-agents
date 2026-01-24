from __future__ import annotations

import json
import re
from typing import Dict, Optional, Any
from dataclasses import dataclass, field

import structlog

from news_fact_checker.evidence.config import EvidenceConfig
from news_fact_checker.evidence.models import DomainReputation
from news_fact_checker.evidence.utils import extract_domain
from news_fact_checker.evidence.constants import (
    STRUCTURAL_SCORES,
    UGC_PENALTY,
    LLM_SCORE_MULTIPLIER_RANGE,
    GOVERNMENT_TLD_PATTERNS,
    ACADEMIC_TLD_PATTERNS,
    COMMERCIAL_TLD_PATTERNS,
    UGC_DOMAIN_PATTERNS,
    CREDIBILITY_TIERS,
)

logger = structlog.get_logger().bind(component="credibility_scorer")

try:
    from ollama import Client as OllamaClient
except ImportError:
    OllamaClient = None


class DomainScorer:

    @staticmethod
    def get_structural_score(domain: str) -> float:
        if not domain:
            return STRUCTURAL_SCORES["default"]

        domain_lower = domain.lower()

        if any(pattern in domain_lower for pattern in GOVERNMENT_TLD_PATTERNS):
            return STRUCTURAL_SCORES["government"]

        if any(pattern in domain_lower for pattern in ACADEMIC_TLD_PATTERNS):
            return STRUCTURAL_SCORES["academic"]

        if domain_lower.endswith(".org"):
            return STRUCTURAL_SCORES["nonprofit"]

        if any(
                domain_lower.endswith(pattern) or pattern in domain_lower
                for pattern in COMMERCIAL_TLD_PATTERNS
        ):
            return STRUCTURAL_SCORES["commercial"]

        return STRUCTURAL_SCORES["default"]

    @staticmethod
    def get_ugc_penalty(domain: str) -> float:
        if not domain:
            return 1.0

        domain_lower = domain.lower()

        if any(pattern in domain_lower for pattern in UGC_DOMAIN_PATTERNS):
            return UGC_PENALTY

        return 1.0


class LLMReputationScorer:

    def __init__(self, config: EvidenceConfig):
        self.config = config
        self.client: Optional[Any] = None

        if config.enable_llm_credibility and OllamaClient:
            try:
                self.client = OllamaClient()
                logger.info("llm_client_initialized")
            except Exception as e:
                logger.warning("llm_init_failed", error=str(e))

    def score_domain(self, domain: str) -> DomainReputation:
        if not self.client:
            return DomainReputation(score=0.6, explanation="LLM disabled")

        try:
            prompt = self._build_prompt(domain)
            response = self.client.chat(
                model=self.config.llm_model,
                messages=[{"role": "user", "content": prompt}],
            )
            content = self._extract_content(response)
            data = self._parse_json(content)

            score = max(0.0, min(1.0, float(data.get("score", 0.6))))
            explanation = data.get("explanation", "No explanation provided")

            return DomainReputation(score=score, explanation=explanation)

        except Exception as e:
            logger.warning("llm_reputation_failed", domain=domain, error=str(e))
            return DomainReputation(score=0.6, explanation=f"Error: {str(e)[:100]}")

    @staticmethod
    def _build_prompt(domain: str) -> str:
        return f"""Rate the factual reliability of this domain for news and verifiable claims.

Domain: {domain}

Consider:
- Is this an official government or academic source?
- Is this an established news organization?
- Does this domain have a reputation for accuracy?

Respond with ONLY valid JSON (no markdown, no extra text):
{{
"score": 0.75,
"explanation": "Brief reason for the score"
}}

Score guidelines:
- 0.9-1.0: Official government/academic sources
- 0.7-0.8: Established reputable news organizations
- 0.5-0.6: General commercial/media sites
- 0.3-0.4: Blogs, opinion sites
- 0.0-0.2: Known unreliable sources

JSON response:"""

    @staticmethod
    def _extract_content(response: Any) -> str:
        if hasattr(response, "message"):
            msg = getattr(response, "message")
            if isinstance(msg, dict):
                return msg.get("content", "") or ""
            if hasattr(msg, "content"):
                return getattr(msg, "content", "") or ""

        if isinstance(response, dict):
            if "message" in response:
                msg = response["message"]
                if isinstance(msg, dict):
                    return msg.get("content", "") or ""

        return str(response)

    @staticmethod
    def _parse_json(text: str) -> Dict[str, Any]:
        text = re.sub(r'```(?:json)?\s*', '', text)
        text = re.sub(r'```\s*$', '', text)
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}") + 1

        if 0 <= start < end:
            json_str = text[start:end]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        return {"score": 0.6, "explanation": "Failed to parse JSON"}


@dataclass
class CredibilityScorer:
    config: EvidenceConfig

    domain_cache: Dict[str, float] = field(default_factory=dict)
    reputation_cache: Dict[str, DomainReputation] = field(default_factory=dict)

    _domain_scorer: Optional[DomainScorer] = None
    _llm_scorer: Optional[LLMReputationScorer] = None

    def __post_init__(self):
        self._domain_scorer = DomainScorer()
        self._llm_scorer = LLMReputationScorer(self.config)

    def score_domain(self, url: str) -> float:
        domain = extract_domain(url)
        if not domain:
            return 0.5

        if domain in self.domain_cache:
            return self.domain_cache[domain]

        structural = self._domain_scorer.get_structural_score(domain)
        ugc_multiplier = self._domain_scorer.get_ugc_penalty(domain)
        llm_multiplier = self._get_llm_adjustment(domain)

        score = structural * ugc_multiplier * llm_multiplier
        score = max(0.0, min(1.0, score))

        self.domain_cache[domain] = score

        logger.debug(
            "domain_scored",
            domain=domain,
            structural=round(structural, 3),
            ugc_mult=round(ugc_multiplier, 3),
            llm_mult=round(llm_multiplier, 3),
            final=round(score, 3),
        )

        return score

    def get_tier(self, url: str) -> int:
        score = self.score_domain(url)

        for tier, (min_score, max_score) in CREDIBILITY_TIERS.items():
            if min_score <= score < max_score:
                return tier

        return 0

    def apply_consensus_feedback(
            self,
            url: str,
            aligned_with_consensus: bool,
            weight: float = 1.0,
    ):
        domain = extract_domain(url)
        if not domain:
            return

        old_score = self.domain_cache.get(domain, 0.6)
        weight = max(0.1, min(2.0, weight))
        step = self.config.consensus_feedback_step * weight

        delta = step if aligned_with_consensus else -step
        new_score = max(0.0, min(1.0, old_score + delta))

        self.domain_cache[domain] = new_score

        logger.debug(
            "consensus_feedback_applied",
            domain=domain,
            old_score=round(old_score, 3),
            new_score=round(new_score, 3),
            aligned=aligned_with_consensus,
        )

    def _get_llm_adjustment(self, domain: str) -> float:
        if not self.config.enable_llm_credibility:
            return 1.0

        if domain in self.reputation_cache:
            reputation = self.reputation_cache[domain]
        else:
            reputation = self._llm_scorer.score_domain(domain)
            self.reputation_cache[domain] = reputation

        min_mult, max_mult = LLM_SCORE_MULTIPLIER_RANGE
        multiplier = min_mult + (max_mult - min_mult) * reputation.score

        return multiplier