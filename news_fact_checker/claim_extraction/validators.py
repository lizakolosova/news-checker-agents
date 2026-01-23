from __future__ import annotations

import re
from typing import Tuple

from news_fact_checker.claim_extraction import patterns
from news_fact_checker.claim_extraction.constants import (
    VERIFIABILITY_BASE_SCORE,
    VERIFIABILITY_ANCHOR_BONUS,
    VERIFIABILITY_HEDGE_PENALTY,
    MIN_VERIFIABILITY_SCORE,
    VAGUE_REFERENTS,
    INTENSIFIERS,
    HEDGE_WORDS,
)
from news_fact_checker.exceptions import VerifiabilityAssessmentError


class VerifiabilityAssessor:

    def __init__(
            self,
            min_score: float = MIN_VERIFIABILITY_SCORE,
            drop_vague_referents: bool = True,
    ):
        self.min_score = min_score
        self.drop_vague_referents = drop_vague_referents

    def assess(self, sentence: str) -> Tuple[float, str]:
        try:
            if not sentence:
                return 0.0, "empty_sentence"

            sentence = sentence.strip()
            sentence_lower = sentence.lower()

            anchors = self._count_anchors(sentence)

            if self.drop_vague_referents and self._has_vague_start(sentence_lower) and anchors == 0:
                return 0.0, "vague_referent_no_anchor"

            if self._has_unanchored_intensifiers(sentence, sentence_lower, anchors):
                return 0.2, "intensifier_without_metric_or_attribution"

            if anchors == 0:
                return 0.1, "no_verification_anchor"

            score = min(1.0, VERIFIABILITY_BASE_SCORE + VERIFIABILITY_ANCHOR_BONUS * anchors)

            if self._has_hedges(sentence_lower):
                score = max(0.0, score - VERIFIABILITY_HEDGE_PENALTY)

            return score, "ok"

        except Exception as e:
            raise VerifiabilityAssessmentError(
                f"Failed to assess verifiability: {e}"
            ) from e

    def is_verifiable(self, sentence: str) -> bool:
        score, _ = self.assess(sentence)
        return score >= self.min_score

    @staticmethod
    def _count_anchors(sentence: str) -> int:
        count = 0

        if patterns.NUMBER_PATTERN.search(sentence):
            count += 1

        if patterns.DATE_PATTERN.search(sentence):
            count += 1

        if patterns.ENTITY_PATTERN.search(sentence):
            count += 1

        if patterns.ATTRIBUTION_PATTERN.search(sentence):
            count += 1

        if patterns.QUOTE_PATTERN.search(sentence):
            count += 1

        return count

    @staticmethod
    def _has_vague_start(sentence_lower: str) -> bool:
        return sentence_lower.startswith(VAGUE_REFERENTS)

    @staticmethod
    def _has_unanchored_intensifiers(
            sentence: str, sentence_lower: str, anchor_count: int
    ) -> bool:
        tokens = set(re.findall(r"[a-z]+", sentence_lower))
        has_intensifier = bool(tokens.intersection(INTENSIFIERS))

        if not has_intensifier:
            return False

        has_number = bool(patterns.NUMBER_PATTERN.search(sentence))
        has_date = bool(patterns.DATE_PATTERN.search(sentence))
        has_attribution = bool(patterns.ATTRIBUTION_PATTERN.search(sentence))

        return not (has_number or has_date or has_attribution)

    @staticmethod
    def _has_hedges(sentence_lower: str) -> bool:
        tokens = set(re.findall(r"[a-z]+", sentence_lower))
        return bool(tokens.intersection(HEDGE_WORDS))