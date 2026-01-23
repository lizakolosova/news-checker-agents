from __future__ import annotations


from news_fact_checker.evidence.constants import (
    BASE_QUALITY_SCORE,
    UNCLEAR_STANCE_SCORE,
    NUMBER_MATCH_BONUS,
    SNIPPET_MIN_LENGTH,
    SNIPPET_PENALTY
)
from news_fact_checker.evidence.utils import extract_numbers, to_float


class QualityAssessor:

    def assess(
            self,
            claim: str,
            snippet: str = "",
            stance: str = "unclear",
    ) -> float:
        if stance not in {"supports", "refutes"}:
            return UNCLEAR_STANCE_SCORE

        score = BASE_QUALITY_SCORE

        if self._has_compatible_numbers(claim, snippet):
            score += NUMBER_MATCH_BONUS

        if self._is_snippet_too_short(snippet):
            score -= SNIPPET_PENALTY

        return max(0.0, min(1.0, score))

    @staticmethod
    def _has_compatible_numbers(claim: str, snippet: str) -> bool:
        claim_numbers = extract_numbers(claim)
        if not claim_numbers:
            return False

        text = f"{claim} {snippet}".lower()
        evidence_numbers = extract_numbers(text)

        for claim_num in claim_numbers:
            claim_val = to_float(claim_num)
            for ev_num in evidence_numbers:
                ev_val = to_float(ev_num)
                rel_diff = abs(claim_val - ev_val) / max(abs(ev_val), 1.0)
                if rel_diff <= 0.15:
                    return True

        return False

    @staticmethod
    def _is_snippet_too_short(snippet: str) -> bool:
        return len(snippet.strip()) < SNIPPET_MIN_LENGTH


def assess_quality(claim: str, snippet: str = "", stance: str = "unclear") -> float:
    assessor = QualityAssessor()
    return assessor.assess(claim, snippet, stance)