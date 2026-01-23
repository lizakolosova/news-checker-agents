from __future__ import annotations

from typing import Tuple

from news_fact_checker.claim_extraction import patterns
from news_fact_checker.claim_extraction.models import ClaimType
from news_fact_checker.claim_extraction.constants import (
    BASE_CONFIDENCE,
    ATTRIBUTION_CONFIDENCE_BONUS,
    STATISTICAL_CONFIDENCE_BONUS,
    TEMPORAL_CONFIDENCE_BONUS,
    CAUSAL_CONFIDENCE_BONUS,
    COMPARATIVE_CONFIDENCE_BONUS,
    FACTUAL_CONFIDENCE_BONUS,
    OPINION_CONFIDENCE_PENALTY,
    DEFINITIVE_CONFIDENCE_BONUS,
    OPINION_MARKERS,
    DEFINITIVE_MARKERS,
)
from news_fact_checker.exceptions import ClaimClassificationError


class ClaimClassifier:

    def classify(self, sentence: str) -> Tuple[ClaimType, float]:
        try:
            if not sentence:
                return ClaimType.FACTUAL, 0.0

            sentence_lower = sentence.lower()
            confidence = BASE_CONFIDENCE

            has_attribution = bool(patterns.ATTRIBUTION_PATTERN.search(sentence))
            has_number = bool(patterns.NUMBER_PATTERN.search(sentence))
            has_date = bool(patterns.DATE_PATTERN.search(sentence))
            has_causal = bool(patterns.CAUSAL_PATTERN.search(sentence))
            has_comparative = bool(patterns.COMPARATIVE_PATTERN.search(sentence))

            if has_attribution:
                claim_type = ClaimType.ATTRIBUTION
                confidence += ATTRIBUTION_CONFIDENCE_BONUS
            elif has_number:
                claim_type = ClaimType.STATISTICAL
                confidence += STATISTICAL_CONFIDENCE_BONUS
            elif has_date:
                claim_type = ClaimType.TEMPORAL
                confidence += TEMPORAL_CONFIDENCE_BONUS
            elif has_causal:
                claim_type = ClaimType.CAUSAL
                confidence += CAUSAL_CONFIDENCE_BONUS
            elif has_comparative:
                claim_type = ClaimType.COMPARATIVE
                confidence += COMPARATIVE_CONFIDENCE_BONUS
            else:
                claim_type = ClaimType.FACTUAL
                confidence += FACTUAL_CONFIDENCE_BONUS

            confidence = self._adjust_confidence(sentence_lower, confidence)

            confidence = max(0.0, min(1.0, confidence))

            return claim_type, confidence

        except Exception as e:
            raise ClaimClassificationError(
                f"Failed to classify sentence: {e}"
            ) from e

    @staticmethod
    def _adjust_confidence(sentence_lower: str, base_confidence: float) -> float:
        confidence = base_confidence
        tokens = set(sentence_lower.split())

        if tokens.intersection(OPINION_MARKERS):
            confidence -= OPINION_CONFIDENCE_PENALTY

        if tokens.intersection(DEFINITIVE_MARKERS):
            confidence += DEFINITIVE_CONFIDENCE_BONUS

        return confidence

    def is_likely_claim(self, sentence: str, min_confidence: float = 0.3) -> bool:
        _, confidence = self.classify(sentence)
        return confidence >= min_confidence