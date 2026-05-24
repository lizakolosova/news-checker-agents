from typing import Tuple

STANCE_LABELS = ("supports", "refutes", "unclear")

CONSENSUS_LEVELS = (
    "strong_support",
    "strong_refutation",
    "likely_true",
    "likely_false",
    "mixed",
    "insufficient"
)

CREDIBILITY_TIERS = {
    1: (0.80, 1.00),
    2: (0.60, 0.80),
    3: (0.40, 0.60),
    0: (0.00, 0.40),
}

STRONG_CONSENSUS_THRESHOLD = 0.75
LIKELY_CONSENSUS_THRESHOLD = 0.60
MIXED_CONSENSUS_THRESHOLD = 0.20
MIN_TOTAL_WEIGHT = 0.03

WEAK_FIT_THRESHOLD = 0.35
STRONG_FIT_DOWNGRADE_THRESHOLD = 0.65

DEFAULT_DOMAIN_WEIGHT = 0.4
DEFAULT_QUALITY_WEIGHT = 0.35
DEFAULT_RECENCY_WEIGHT = 0.25

STRUCTURAL_SCORES = {
    "government": 0.92,
    "academic": 0.88,
    "nonprofit": 0.78,
    "commercial": 0.70,
    "default": 0.60,
}

UGC_PENALTY = 0.50

LLM_SCORE_MULTIPLIER_RANGE = (0.8, 1.2)

NUMBER_COMPATIBILITY_THRESHOLD = 0.15
MIN_TERM_OVERLAP_COUNT = 2
MIN_TERM_OVERLAP_RATIO = 0.3
MIN_KEY_TERM_LENGTH = 4

SNIPPET_MIN_LENGTH = 40
SNIPPET_PENALTY = 0.15
NUMBER_MATCH_BONUS = 0.25
BASE_QUALITY_SCORE = 0.5
UNCLEAR_STANCE_SCORE = 0.35

GOVERNMENT_TLD_PATTERNS: Tuple[str, ...] = (
    ".gov.", ".gov", ".gouv.", ".parliament", ".europa.eu",
    ".int", ".senate", ".congress"
)

ACADEMIC_TLD_PATTERNS: Tuple[str, ...] = (
    ".edu", ".ac.", ".university"
)

COMMERCIAL_TLD_PATTERNS: Tuple[str, ...] = (
    ".com", ".net", ".co."
)

UGC_DOMAIN_PATTERNS: Tuple[str, ...] = (
    "facebook.com", "instagram.com", "tiktok.com", "twitter.com",
    "x.com", "reddit.com", "quora.com", "medium.com", "substack.com",
    "blogspot.", "wordpress.com", "patreon.com", "tumblr.com",
)

SUPPORT_CUES: Tuple[str, ...] = (
    "confirms", "confirmed", "showed", "shows", "found", "finds",
    "rose to", "fell to", "increased to", "decreased to", "was", "were",
    "reached", "up to", "down to", "remained at", "unchanged at",
    "according to", "reported", "announced", "stated", "data shows",
    "statistics show", "grossed", "earned", "box office", "scored",
    "won", "defeated", "beat",
)

REFUTE_CUES: Tuple[str, ...] = (
    "false", "falsely", "debunked", "debunks", "incorrect", "wrong",
    "misleading", "no evidence_evaluation", "denied", "deny", "denies", "did not",
    "didn't", "has not", "haven't", "never happened", "contradicts",
    "disputed", "disputes",
)

ATTRIBUTION_PATTERNS: Tuple[str, ...] = (
    "according to", "said", "stated", "reports", "reported", "announced", "data from"
)

AUTHORITY_PENALTY_DEFAULT = 0.40
AUTHORITY_PENALTY_GOVERNMENT = 0.75

TEMPORAL_PENALTY_YEAR_MISMATCH = 0.10
TEMPORAL_PENALTY_MONTH_MISMATCH = 0.35

MONTHS: Tuple[str, ...] = (
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december"
)

CONSENSUS_DESCRIPTIONS = {
    "strong_support": "strongly supported by credible sources",
    "strong_refutation": "clearly contradicted by evidence_evaluation",
    "likely_true": "likely accurate based on available evidence_evaluation",
    "likely_false": "likely inaccurate based on available evidence_evaluation",
    "mixed": "evidence_evaluation shows conflicting information",
    "insufficient": "insufficient evidence_evaluation to determine accuracy",
}

HIGH_CONFIDENCE_THRESHOLD = 80
MODERATE_CONFIDENCE_THRESHOLD = 60

IMPLICIT_REFUTATION_CONFIDENCE_BASE = 0.5
IMPLICIT_REFUTATION_CONFIDENCE_MULTIPLIER = 0.5
IMPLICIT_REFUTATION_CONFIDENCE_CAP = 0.75