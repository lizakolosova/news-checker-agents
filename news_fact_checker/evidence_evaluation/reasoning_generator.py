from __future__ import annotations

from typing import List, Dict, Optional

from news_fact_checker.evidence_evaluation.models import EvaluatedSource
from news_fact_checker.evidence_evaluation.utils import normalize_confidence, count_by_key
from news_fact_checker.evidence_evaluation.constants import (
    CONSENSUS_DESCRIPTIONS,
    HIGH_CONFIDENCE_THRESHOLD,
    MODERATE_CONFIDENCE_THRESHOLD,
)


class StanceAnalyzer:

    @staticmethod
    def count_stances(sources: List[EvaluatedSource]) -> Dict[str, int]:
        return count_by_key(sources, "stance", {"supports", "refutes", "unclear"})


class TierAnalyzer:

    @staticmethod
    def get_distribution(sources: List[EvaluatedSource]) -> Dict[int, int]:
        tiers = {1: 0, 2: 0, 3: 0, 0: 0}
        for source in sources:
            tier = source.get("credibility_tier", 0)
            if tier in tiers:
                tiers[tier] += 1
        return tiers


class CredibilityAnalyzer:

    @staticmethod
    def calculate_average(sources: List[EvaluatedSource]) -> float:
        if not sources:
            return 0.0
        total = sum(source.get("credibility_score", 0.5) for source in sources)
        return total / len(sources)


class ReasoningBuilder:

    def __init__(self):
        self.stance_analyzer = StanceAnalyzer()
        self.tier_analyzer = TierAnalyzer()
        self.credibility_analyzer = CredibilityAnalyzer()

    def build(
            self,
            claim: str,
            sources: List[EvaluatedSource],
            consensus: str,
            confidence: Optional[float] = None,
    ) -> str:
        if not sources:
            return (
                "No reliable evidence_evaluation sources were found to evaluate this claim. "
                "Without supporting or refuting evidence_evaluation, the claim cannot be verified."
            )

        parts = [self._get_consensus_statement(consensus), self._get_source_description(sources)]

        if consensus in {"mixed", "insufficient"}:
            parts.append(self._get_stance_breakdown(sources))

        parts.append(self._get_consensus_elaboration(consensus))
        parts.append(self._get_confidence_statement(confidence))

        return " ".join(parts)

    @staticmethod
    def _get_consensus_statement(consensus: str) -> str:
        description = CONSENSUS_DESCRIPTIONS.get(
            consensus, "unclear evidence_evaluation"
        )
        return f"This claim is {description}."

    def _get_source_description(self, sources: List[EvaluatedSource]) -> str:
        num_sources = len(sources)
        tier_dist = self.tier_analyzer.get_distribution(sources)
        avg_cred = self.credibility_analyzer.calculate_average(sources)

        if tier_dist[1] > 0:
            return (
                f"Analysis is based on {num_sources} source{'s' if num_sources != 1 else ''}, "
                f"including {tier_dist[1]} highly credible source{'s' if tier_dist[1] != 1 else ''} "
                f"(government, academic, or official organizations)."
            )
        else:
            return (
                f"Analysis is based on {num_sources} source{'s' if num_sources != 1 else ''} "
                f"with average credibility score of {avg_cred:.0%}."
            )

    def _get_stance_breakdown(self, sources: List[EvaluatedSource]) -> str:
        stance_counts = self.stance_analyzer.count_stances(sources)
        return (
            f"Evidence includes {stance_counts['supports']} supporting source{'s' if stance_counts['supports'] != 1 else ''}, "
            f"{stance_counts['refutes']} refuting source{'s' if stance_counts['refutes'] != 1 else ''}, "
            f"and {stance_counts['unclear']} with unclear stance."
        )

    @staticmethod
    def _get_consensus_elaboration(consensus: str) -> str:
        elaborations = {
            "strong_support": (
                "Multiple independent sources confirm the key facts in this claim."
            ),
            "strong_refutation": (
                "Multiple sources directly contradict the central facts of this claim."
            ),
            "likely_true": (
                "While not definitively proven, the preponderance of evidence_evaluation supports this claim."
            ),
            "likely_false": (
                "While not definitively disproven, the preponderance of evidence_evaluation contradicts this claim."
            ),
            "mixed": (
                "Different credible sources provide conflicting information, "
                "suggesting the claim may be partially accurate or context-dependent."
            ),
            "insufficient": (
                "Available evidence_evaluation is too limited or unclear to make a determination."
            ),
        }
        return elaborations.get(consensus, "")

    @staticmethod
    def _get_confidence_statement(confidence: Optional[float]) -> str:
        if confidence is None:
            return ""

        conf_pct = normalize_confidence(confidence)

        if conf_pct >= HIGH_CONFIDENCE_THRESHOLD:
            return f"Confidence in this assessment is high ({conf_pct}%)."
        elif conf_pct >= MODERATE_CONFIDENCE_THRESHOLD:
            return f"Confidence in this assessment is moderate ({conf_pct}%)."
        else:
            return f"Confidence in this assessment is low ({conf_pct}%)."


class ReasoningGenerator:

    def __init__(self):
        self.builder = ReasoningBuilder()

    def generate(
            self,
            claim: str,
            sources: List[EvaluatedSource],
            consensus: str,
            confidence: Optional[float] = None,
    ) -> str:
        return self.builder.build(claim, sources, consensus, confidence)


def generate_reasoning(
        claim: str,
        sources: List[EvaluatedSource],
        consensus: str,
        confidence: Optional[float] = None,
) -> str:
    generator = ReasoningGenerator()
    return generator.generate(claim, sources, consensus, confidence)