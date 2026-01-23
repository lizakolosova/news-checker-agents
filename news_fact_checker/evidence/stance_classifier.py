from __future__ import annotations

import structlog

from news_fact_checker.evidence.models import StanceResult
from news_fact_checker.evidence.utils import (
    numbers_compatible,
    calculate_term_overlap,
)
from news_fact_checker.evidence.constants import (
    SUPPORT_CUES,
    REFUTE_CUES,
    MIN_TERM_OVERLAP_COUNT,
    MIN_TERM_OVERLAP_RATIO,
)

logger = structlog.get_logger().bind(component="stance_classifier")


class StanceClassifier:

    def __init__(self):
        self.support_cues = set(SUPPORT_CUES)
        self.refute_cues = set(REFUTE_CUES)

    def classify(
            self,
            claim_text: str,
            snippet: str,
            source_url: str = "",
            source_title: str = "",
    ) -> StanceResult:
        if not claim_text or not snippet:
            return StanceResult(
                label="unclear",
                confidence=0.3,
                reason="Insufficient text for classification",
            )

        claim_lower = claim_text.lower()
        evidence_text = f"{source_title or ''} {snippet or ''}".lower()

        if self._has_refutation_language(evidence_text):
            return StanceResult(
                label="refutes",
                confidence=0.8,
                reason="Evidence uses explicit refutation/denial language",
            )

        if not numbers_compatible(claim_lower, evidence_text):
            return StanceResult(
                label="unclear",
                confidence=0.55,
                reason="Numbers/dates in evidence differ substantially from the claim",
            )

        has_support_cues = self._has_support_language(evidence_text)
        has_term_overlap = self._has_sufficient_overlap(claim_lower, evidence_text)

        if has_support_cues and has_term_overlap:
            return StanceResult(
                label="supports",
                confidence=0.75,
                reason="Evidence language and key terms align with the claim",
            )

        return StanceResult(
            label="unclear",
            confidence=0.55,
            reason="Evidence is not explicit enough to support or refute",
        )

    def _has_refutation_language(self, text: str) -> bool:
        return any(cue in text for cue in self.refute_cues)

    def _has_support_language(self, text: str) -> bool:
        return any(cue in text for cue in self.support_cues)

    @staticmethod
    def _has_sufficient_overlap(claim: str, evidence: str) -> bool:
        overlap_count, overlap_ratio = calculate_term_overlap(claim, evidence)
        return (
                overlap_count >= MIN_TERM_OVERLAP_COUNT or
                overlap_ratio >= MIN_TERM_OVERLAP_RATIO
        )


def classify_stance(
        claim_text: str,
        snippet: str,
        source_url: str = "",
        source_title: str = "",
) -> StanceResult:
    classifier = StanceClassifier()
    return classifier.classify(claim_text, snippet, source_url, source_title)