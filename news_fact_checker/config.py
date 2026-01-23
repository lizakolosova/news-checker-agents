from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Set, Tuple


@dataclass
class ClaimExtractionConfig:
    min_confidence: float = 0.5
    similarity_threshold: float = 0.85
    context_window: int = 1
    min_sub_claim_words: int = 4
    sub_claim_confidence_multiplier: float = 0.8
    log_level: str = "INFO"

    min_verifiability: float = 0.35
    drop_unverifiable: bool = True

    drop_vague_referents: bool = True
    vague_referents: Tuple[str, ...] = (
        "this", "that", "these", "those", "it", "they", "there", "such"
    )


@dataclass
class ResearchConfig:

    max_results: int = 5
    per_query_results: int = 5
    search_api_key: str = os.getenv("SERPER_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")

    min_relevance: float = 0.20
    keep_top_k_if_all_filtered: int = 2

    prefer_authority_domains: bool = True
    authority_domain_patterns: Tuple[str, ...] = (
        r"\.gov(\.|$)",
        r"\.gov\.[a-z]{2}$",
        r"\.edu(\.|$)",
        r"\.ac\.[a-z]{2}$",
        r"\.int(\.|$)",
        r"\.eu(\.|$)",
    )

    multilateral_domains: Tuple[str, ...] = (
        "who.int",
        "imf.org",
        "worldbank.org",
        "oecd.org",
        "un.org",
        "europa.eu",
        "ec.europa.eu",
    )

    low_signal_domains: Tuple[str, ...] = (
        "facebook.com",
        "twitter.com",
        "x.com",
        "reddit.com",
        "quora.com",
        "answers.yahoo.com",
        "ask.com",
    )

    llm_retry_on_429: bool = True
    llm_max_retries: int = 2
    llm_retry_delay_seconds: float = 2.0

    loglevel: str = "INFO"


@dataclass
class EvidenceConfig:

    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))

    domain_weight: float = 0.5
    quality_weight: float = 0.3
    recency_weight: float = 0.2

    model_name: str = "llama-3.3-70b-versatile"
    temperature: float = 0.1
    max_tokens_quality: int = 10
    max_tokens_reasoning: int = 200

    strong_consensus_threshold: float = 0.80
    likely_consensus_threshold: float = 0.65

    min_tier1_sources_for_strong: int = 1
    min_total_sources: int = 2

    poor_fit_threshold: float = 0.35
    weak_fit_threshold: float = 0.50

    tier1_sources: Set[str] = field(default_factory=lambda: {
        'reuters.com', 'apnews.com', 'afp.com', 'ap.org',
        'bbc.com', 'bbc.co.uk', 'pbs.org', 'npr.org', 'c-span.org',

        'nature.com', 'science.org', 'sciencedirect.com', 'nejm.org',
        'thelancet.com', 'bmj.com', 'plos.org', 'springer.com',

        'nih.gov', 'cdc.gov', 'fda.gov', 'nasa.gov', 'noaa.gov',
        'census.gov', 'bls.gov', 'dol.gov', 'sec.gov', 'ftc.gov',
        'federalreserve.gov',
        '.gov', '.edu', '.mil',

        'who.int', 'europa.eu', 'ec.europa.eu', 'eurostat',
        'ecb.europa.eu', 'imf.org', 'worldbank.org', 'oecd.org',

        'statbel.fgov.be', 'nbb.be',
        'ons.gov.uk',
        'destatis.de',
        'insee.fr',
        'istat.it',

        'bloomberg.com', 'ft.com', 'wsj.com',
    })

    tier2_sources: Set[str] = field(default_factory=lambda: {
        'nytimes.com', 'washingtonpost.com', 'usatoday.com',
        'latimes.com', 'chicagotribune.com', 'bostonglobe.com',
        'theguardian.com', 'telegraph.co.uk', 'independent.co.uk',

        'economist.com', 'theatlantic.com', 'newyorker.com',
        'foreignaffairs.com', 'time.com',

        'forbes.com', 'businessinsider.com', 'cnbc.com',
        'arstechnica.com', 'theverge.com', 'wired.com',
    })

    tier3_sources: Set[str] = field(default_factory=lambda: {
        'buzzfeed.com', 'huffpost.com', 'mashable.com',
        'vice.com', 'vox.com', 'politico.com', 'axios.com'
    })

    low_credibility_sources: Set[str] = field(default_factory=lambda: {
        'infowars.com', 'naturalnews.com', 'beforeitsnews.com',
        'quora.com', 'reddit.com',
    })

    def __post_init__(self):
        total_weight = self.domain_weight + self.quality_weight + self.recency_weight
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Scoring weights must sum to 1.0, got {total_weight:.3f}")


@dataclass
class VerdictConfig:

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