"""
Production-ready configuration with conservative defaults.

KEY CHANGES:
1. Higher quality thresholds
2. Require Tier-1 sources for strong verdicts
3. Stricter consensus thresholds
4. Better rate limit handling
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Set, Tuple


@dataclass
class ClaimExtractionConfig:
    """Configuration for claim extraction agent."""
    min_confidence: float = 0.5
    similarity_threshold: float = 0.85
    context_window: int = 1
    min_sub_claim_words: int = 4
    sub_claim_confidence_multiplier: float = 0.8
    log_level: str = "INFO"

    # Verifiability gating
    min_verifiability: float = 0.35
    drop_unverifiable: bool = True

    # Vague claim suppression
    drop_vague_referents: bool = True
    vague_referents: Tuple[str, ...] = (
        "this", "that", "these", "those", "it", "they", "there", "such"
    )


@dataclass
class ResearchConfig:
    """Configuration for Research Agent (PRODUCTION MODE)."""

    # Search settings
    max_results: int = 5  # Sources per claim
    per_query_results: int = 5  # Results per query
    search_api_key: str = os.getenv("SERPER_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")

    # Relevance filtering (STRICTER)
    min_relevance: float = 0.20  # Raised from 0.15
    keep_top_k_if_all_filtered: int = 2  # Reduced from 3

    # Authority domain patterns
    prefer_authority_domains: bool = True
    authority_domain_patterns: Tuple[str, ...] = (
        r"\.gov(\.|$)",
        r"\.gov\.[a-z]{2}$",
        r"\.edu(\.|$)",
        r"\.ac\.[a-z]{2}$",
        r"\.int(\.|$)",
        r"\.eu(\.|$)",
    )

    # Multilateral/international organizations
    multilateral_domains: Tuple[str, ...] = (
        "who.int",
        "imf.org",
        "worldbank.org",
        "oecd.org",
        "un.org",
        "europa.eu",
        "ec.europa.eu",
    )

    # Low-signal domain blacklist (EXPANDED)
    low_signal_domains: Tuple[str, ...] = (
        "facebook.com",
        "twitter.com",
        "x.com",
        "reddit.com",
        "quora.com",  # NEW
        "answers.yahoo.com",  # NEW
        "ask.com",  # NEW
    )

    # Rate limit handling (NEW)
    llm_retry_on_429: bool = True
    llm_max_retries: int = 2
    llm_retry_delay_seconds: float = 2.0

    loglevel: str = "INFO"


@dataclass
class EvidenceConfig:
    """Configuration for Evidence Evaluation Agent (PRODUCTION MODE)."""

    # API Keys
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))

    # Scoring weights (must sum to 1.0)
    domain_weight: float = 0.5  # Increased from 0.4
    quality_weight: float = 0.3  # Decreased from 0.4
    recency_weight: float = 0.2

    # Model configuration
    model_name: str = "llama-3.3-70b-versatile"
    temperature: float = 0.1
    max_tokens_quality: int = 10
    max_tokens_reasoning: int = 200

    # Consensus thresholds (STRICTER)
    strong_consensus_threshold: float = 0.80  # Raised from 0.75
    likely_consensus_threshold: float = 0.65  # Raised from 0.60

    # Minimum requirements (NEW)
    min_tier1_sources_for_strong: int = 1  # Require at least 1 Tier-1 source
    min_total_sources: int = 2  # Require at least 2 sources

    # Evidence fit thresholds (NEW)
    poor_fit_threshold: float = 0.35  # Below this → likely_false
    weak_fit_threshold: float = 0.50  # Below this → downgrade consensus

    # Source credibility tiers
    tier1_sources: Set[str] = field(default_factory=lambda: {
        # News Agencies
        'reuters.com', 'apnews.com', 'afp.com', 'ap.org',
        'bbc.com', 'bbc.co.uk', 'pbs.org', 'npr.org', 'c-span.org',

        # Scientific/Academic
        'nature.com', 'science.org', 'sciencedirect.com', 'nejm.org',
        'thelancet.com', 'bmj.com', 'plos.org', 'springer.com',

        # Government (US)
        'nih.gov', 'cdc.gov', 'fda.gov', 'nasa.gov', 'noaa.gov',
        'census.gov', 'bls.gov', 'dol.gov', 'sec.gov', 'ftc.gov',
        'federalreserve.gov',
        '.gov', '.edu', '.mil',

        # International/EU
        'who.int', 'europa.eu', 'ec.europa.eu', 'eurostat',
        'ecb.europa.eu', 'imf.org', 'worldbank.org', 'oecd.org',

        # National Statistics (Europe)
        'statbel.fgov.be', 'nbb.be',  # Belgium
        'ons.gov.uk',  # UK
        'destatis.de',  # Germany
        'insee.fr',  # France
        'istat.it',  # Italy

        # Financial
        'bloomberg.com', 'ft.com', 'wsj.com',
    })

    tier2_sources: Set[str] = field(default_factory=lambda: {
        # Major Newspapers
        'nytimes.com', 'washingtonpost.com', 'usatoday.com',
        'latimes.com', 'chicagotribune.com', 'bostonglobe.com',
        'theguardian.com', 'telegraph.co.uk', 'independent.co.uk',

        # Quality Magazines
        'economist.com', 'theatlantic.com', 'newyorker.com',
        'foreignaffairs.com', 'time.com',

        # Business/Tech
        'forbes.com', 'businessinsider.com', 'cnbc.com',
        'arstechnica.com', 'theverge.com', 'wired.com',
    })

    tier3_sources: Set[str] = field(default_factory=lambda: {
        'buzzfeed.com', 'huffpost.com', 'mashable.com',
        'vice.com', 'vox.com', 'politico.com', 'axios.com'
    })

    low_credibility_sources: Set[str] = field(default_factory=lambda: {
        'infowars.com', 'naturalnews.com', 'beforeitsnews.com',
        'quora.com', 'reddit.com',  # NEW
    })

    def __post_init__(self):
        """Validate configuration."""
        total_weight = self.domain_weight + self.quality_weight + self.recency_weight
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Scoring weights must sum to 1.0, got {total_weight:.3f}")


@dataclass
class VerdictConfig:
    """Configuration for Verdict Agent (NEW)."""

    true_min_confidence: float = 0.80
    mostly_true_min_confidence: float = 0.65
    mostly_false_min_confidence: float = 0.65

    require_tier1_for_true: bool = True
    min_supporting_sources_for_true: int = 2

    use_llm_explanations: bool = True
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 150


DEFAULT_CONFIG = ClaimExtractionConfig()
DEFAULT_RESEARCH_CONFIG = ResearchConfig()
DEFAULT_EVIDENCE_CONFIG = EvidenceConfig()
DEFAULT_VERDICT_CONFIG = VerdictConfig()