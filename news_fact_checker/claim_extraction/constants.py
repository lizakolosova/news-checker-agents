from typing import Set, Tuple

MIN_VERIFIABILITY_SCORE = 0.35
VERIFIABILITY_BASE_SCORE = 0.25
VERIFIABILITY_ANCHOR_BONUS = 0.2
VERIFIABILITY_HEDGE_PENALTY = 0.15

HIGH_CONFIDENCE_THRESHOLD = 0.8
MEDIUM_CONFIDENCE_THRESHOLD = 0.5
BASE_CONFIDENCE = 0.4

ATTRIBUTION_CONFIDENCE_BONUS = 0.35
STATISTICAL_CONFIDENCE_BONUS = 0.3
TEMPORAL_CONFIDENCE_BONUS = 0.25
CAUSAL_CONFIDENCE_BONUS = 0.2
COMPARATIVE_CONFIDENCE_BONUS = 0.2
FACTUAL_CONFIDENCE_BONUS = 0.1
OPINION_CONFIDENCE_PENALTY = 0.2
DEFINITIVE_CONFIDENCE_BONUS = 0.1

MIN_SUB_CLAIM_WORDS = 3
SUB_CLAIM_CONFIDENCE_MULTIPLIER = 0.9

DEFAULT_SIMILARITY_THRESHOLD = 0.85

DEFAULT_CONTEXT_WINDOW = 2

ENTITY_STOP_WORDS: Set[str] = {
    "The", "This", "That", "These", "Those", "A", "An", "And", "But", "Or",
    "In", "On", "At", "By", "From", "To", "As", "It", "Its", "Their", "They",
}

MONTH_NAMES: Set[str] = {
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
}

VAGUE_REFERENTS: Tuple[str, ...] = (
    "this", "that", "these", "those", "it", "they", "there", "such"
)

INTENSIFIERS: Set[str] = {
    "significant", "dramatic", "remarkable", "substantial",
    "huge", "massive", "major", "sharp"
}

HEDGE_WORDS: Set[str] = {
    "may", "might", "could", "possibly", "perhaps",
    "appears", "seems", "reportedly", "allegedly"
}

OPINION_MARKERS: Set[str] = {
    "may", "might", "could", "possibly", "perhaps", "seems"
}

DEFINITIVE_MARKERS: Set[str] = {
    "is", "are", "was", "were", "has", "have"
}