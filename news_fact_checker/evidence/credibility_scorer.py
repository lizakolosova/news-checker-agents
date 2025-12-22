"""Source credibility assessment based on domain reputation.

This module provides structural heuristics and optional LLM-based domain reputation
scoring without relying on hard-coded tier lists.

Public API:
    - assess_domain_credibility(url) -> float in [0, 1]
    - get_tier(url) -> int (1, 2, 3, or 0 for low credibility)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from urllib.parse import urlparse

import structlog

from news_fact_checker.config import EvidenceConfig

logger = structlog.get_logger().bind(component="credibility_scorer")

try:
    from ollama import Client as OllamaClient
except ImportError:
    OllamaClient = None


def _extract_domain(url: str) -> str:
    """Extract and normalize domain from URL."""
    if not url:
        return ""
    try:
        domain = urlparse(url).netloc.lower()
        return domain.replace("www.", "")
    except Exception:
        return ""


def _structural_score(domain: str) -> float:
    """
    Calculate baseline credibility score from TLD and URL patterns.

    Returns:
        float: Score in [0.6, 0.92] based on domain structure
    """
    if not domain:
        return 0.5

    domain_lower = domain.lower()

    gov_patterns = (
        ".gov.", ".gov", ".gouv.", ".parliament", ".europa.eu",
        ".int", ".senate", ".congress"
    )
    if any(pattern in domain_lower for pattern in gov_patterns):
        return 0.92

    edu_patterns = (".edu", ".ac.", ".university")
    if any(pattern in domain_lower for pattern in edu_patterns):
        return 0.88

    if domain_lower.endswith(".org"):
        return 0.78

    commercial_patterns = (".com", ".net", ".co.")
    if any(domain_lower.endswith(pattern) or pattern in domain_lower
           for pattern in commercial_patterns):
        return 0.70

    return 0.60


def _ugc_penalty_multiplier(domain: str) -> float:
    """
    Apply penalty for user-generated content and social media platforms.

    Returns:
        float: Multiplier in [0.5, 1.0] where 0.5 is maximum penalty
    """
    if not domain:
        return 1.0

    domain_lower = domain.lower()

    low_credibility_patterns = (
        "facebook.com", "instagram.com", "tiktok.com", "twitter.com",
        "x.com", "reddit.com", "quora.com", "medium.com", "substack.com",
        "blogspot.", "wordpress.com", "patreon.com", "tumblr.com",
    )

    if any(pattern in domain_lower for pattern in low_credibility_patterns):
        return 0.50

    return 1.00


def _extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Robustly extract JSON object from text that may contain extra content.

    Handles:
        - Markdown code blocks
        - Text before/after JSON
        - Malformed JSON with missing braces
        - Newlines and escaped characters

    Returns:
        dict: Parsed JSON object

    Raises:
        ValueError: If no valid JSON can be extracted
    """
    if not text:
        raise ValueError("Empty text provided")

    text = re.sub(r'```(?:json)?\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}") + 1

    if start == -1:
        raise ValueError("No opening brace '{' found in text")

    if end <= start:
        raise ValueError("No closing brace '}' found after opening brace")

    json_str = text[start:end]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        open_braces = json_str.count("{")
        close_braces = json_str.count("}")

        if close_braces < open_braces:
            json_str += "}" * (open_braces - close_braces)
            return json.loads(json_str)

        raise ValueError(f"Could not parse JSON from text: {text[:200]}")


def _normalize_llm_response(response: Any) -> str:
    """
    Normalize various LLM client response formats to plain text.

    Supports:
        - Ollama Response objects with .message attribute
        - Ollama dict responses: {"message": {"content": "..."}}
        - OpenAI/Groq ChatCompletion objects
        - Raw string responses

    Returns:
        str: Extracted content text
    """
    if not response:
        return ""

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

        if "choices" in response:
            try:
                choice = response["choices"][0]
                msg = choice.get("message", {})
                return msg.get("content", "") or ""
            except (IndexError, KeyError, TypeError):
                pass

        if "content" in response:
            return response.get("content", "") or ""

    if hasattr(response, "choices"):
        try:
            choice = response.choices[0]
            msg = getattr(choice, "message", None)
            if msg and hasattr(msg, "content"):
                return msg.content or ""
        except (IndexError, AttributeError):
            pass

    return str(response)


def _build_reputation_prompt(domain: str) -> str:
    """Build prompt for LLM domain reputation query."""
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


@dataclass
class CredibilityScorer:
    """
    Domain credibility scorer using structural heuristics and optional LLM enhancement.

    Scoring components:
        1. Structural signals (TLD, domain patterns)
        2. UGC/social media penalties
        3. Optional LLM reputation scoring
        4. Optional consensus-based feedback

    Tier mapping:
        - Tier 1 (score >= 0.80): Highly credible (government, academic)
        - Tier 2 (0.60-0.80): Credible (established media, organizations)
        - Tier 3 (0.40-0.60): Moderate credibility
        - Tier 0 (< 0.40): Low credibility (UGC, unverified sources)
    """

    config: EvidenceConfig
    llm_client: Optional[Any] = None

    domain_score_cache: Dict[str, float] = field(default_factory=dict)
    llm_reputation_cache: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize optional LLM client for domain reputation scoring."""
        if OllamaClient is None:
            logger.info("ollama_unavailable", reason="ollama package not installed")
            self.llm_client = None
            return

        try:
            self.llm_client = OllamaClient()
            logger.info("ollama_client_initialized", status="success")
        except Exception as e:
            logger.warning(
                "ollama_init_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            self.llm_client = None

    def assess_domain_credibility(self, url: str) -> float:
        """
        Assess credibility score for a URL's domain.

        Args:
            url: Full URL to assess

        Returns:
            float: Credibility score in [0, 1]
        """
        domain = _extract_domain(url)
        if not domain:
            return 0.5

        if domain in self.domain_score_cache:
            return self.domain_score_cache[domain]

        score = self._score_domain(domain)
        self.domain_score_cache[domain] = score
        return score

    def get_tier(self, url: str) -> int:
        """
        Map credibility score to tier level.

        Args:
            url: Full URL to assess

        Returns:
            int: Tier level (1=highest, 0=lowest)
        """
        score = self.assess_domain_credibility(url)

        if score >= 0.80:
            return 1
        if score >= 0.60:
            return 2
        if score >= 0.40:
            return 3
        return 0

    def update_from_consensus(
        self,
        url: str,
        aligned_with_consensus: bool,
        weight: float = 1.0,
    ) -> None:
        """
        Update domain score based on consensus feedback (optional).

        This allows the system to learn from high-confidence consensus verdicts.
        Small adjustments prevent overfitting.

        Args:
            url: Source URL
            aligned_with_consensus: Whether source aligned with consensus
            weight: Adjustment weight (clamped to [0.1, 2.0])
        """
        domain = _extract_domain(url)
        if not domain:
            return

        old_score = self.domain_score_cache.get(domain, 0.6)

        weight = max(0.1, min(2.0, weight))
        step = 0.03 * weight

        delta = step if aligned_with_consensus else -step
        new_score = max(0.0, min(1.0, old_score + delta))

        self.domain_score_cache[domain] = new_score

        logger.debug(
            "consensus_feedback_applied",
            domain=domain,
            old_score=round(old_score, 3),
            new_score=round(new_score, 3),
            aligned=aligned_with_consensus,
        )

    def _score_domain(self, domain: str) -> float:
        """
        Combine all scoring signals into final credibility score.

        Components:
            - Structural score from TLD/patterns
            - UGC penalty multiplier
            - Optional LLM adjustment multiplier

        Returns:
            float: Final score in [0, 1]
        """
        structural = _structural_score(domain)
        ugc_multiplier = _ugc_penalty_multiplier(domain)
        llm_multiplier = self._llm_adjustment(domain)

        score = structural * ugc_multiplier * llm_multiplier
        score = max(0.0, min(1.0, score))

        logger.debug(
            "domain_scored",
            domain=domain,
            structural=round(structural, 3),
            ugc_mult=round(ugc_multiplier, 3),
            llm_mult=round(llm_multiplier, 3),
            final=round(score, 3),
        )

        return score


    def _llm_adjustment(self, domain: str) -> float:
        """
        Use LLM to provide reputation-based adjustment.

        Returns:
            float: Multiplier in [0.8, 1.2], centered at 1.0 (neutral)
        """
        if not self.llm_client:
            return 1.0

        # Check cache
        if domain in self.llm_reputation_cache:
            return self.llm_reputation_cache[domain]

        try:
            reputation = self._query_llm_for_domain(domain)
            score = reputation.get("score", 0.6)

            # Validate score is in [0, 1]
            score = max(0.0, min(1.0, float(score)))

            # Map [0, 1] to multiplier [0.8, 1.2]
            multiplier = 0.8 + 0.4 * score

            logger.debug(
                "llm_reputation_scored",
                domain=domain,
                score=round(score, 3),
                multiplier=round(multiplier, 3),
                explanation=reputation.get("explanation", "")[:100],
            )

        except Exception as e:
            logger.warning(
                "llm_reputation_failed",
                domain=domain,
                error=str(e),
                error_type=type(e).__name__,
            )
            multiplier = 1.0  # Neutral fallback

        self.llm_reputation_cache[domain] = multiplier
        return multiplier

    def _query_llm_for_domain(self, domain: str) -> Dict[str, Any]:
        """
        Query LLM for domain reputation assessment.

        Args:
            domain: Domain to assess

        Returns:
            dict: {"score": float, "explanation": str}

        Raises:
            Exception: If LLM call or parsing fails
        """
        prompt = _build_reputation_prompt(domain)

        try:
            response = self.llm_client.chat(
                model="llama3",
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:
            logger.error(
                "llm_call_failed",
                domain=domain,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

        try:
            content = _normalize_llm_response(response)
        except Exception as e:
            logger.error(
                "llm_response_normalization_failed",
                domain=domain,
                raw_response=str(response)[:300],
                error=str(e),
            )
            raise

        try:
            data = _extract_json_from_text(content)
        except Exception as e:
            logger.warning(
                "llm_json_parse_failed",
                domain=domain,
                content_preview=content[:400],
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "score": 0.6,
                "explanation": f"Parse error: {str(e)[:100]}",
            }

        if "score" not in data:
            logger.warning(
                "llm_response_missing_score",
                domain=domain,
                data=data,
            )
            data["score"] = 0.6

        if "explanation" not in data:
            data["explanation"] = "No explanation provided"

        return data

