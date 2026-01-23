from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from news_fact_checker.evidence.models import EvaluatedSource, EvaluationResult
from news_fact_checker.evidence.utils import safe_float


class RecencyScorer:

    @staticmethod
    def score(published_date: Optional[str]) -> float:
        if not published_date:
            return 0.7

        try:
            pub_date = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
            now = datetime.now(pub_date.tzinfo)
            age_days = (now - pub_date).days

            if age_days < 30:
                return 1.0
            elif age_days < 90:
                return 0.9
            elif age_days < 365:
                return 0.8
            elif age_days < 730:
                return 0.7
            else:
                return 0.6
        except (ValueError, AttributeError):
            return 0.7


class FitScorer:

    @staticmethod
    def score(claim: str, evidence: dict) -> float:
        claim_lower = claim.lower()
        snippet = (evidence.get("snippet", "") or "").lower()
        title = (evidence.get("source_title", "") or "").lower()

        combined_text = f"{title} {snippet}"

        claim_words = set(claim_lower.split())
        evidence_words = set(combined_text.split())

        if not claim_words:
            return 0.5

        overlap = claim_words & evidence_words
        overlap_ratio = len(overlap) / len(claim_words)

        if overlap_ratio > 0.7:
            return 1.0
        elif overlap_ratio > 0.5:
            return 0.85
        elif overlap_ratio > 0.3:
            return 0.7
        elif overlap_ratio > 0.15:
            return 0.5
        else:
            return 0.3


class AggregationScorer:

    @staticmethod
    def calculate_overall_credibility(sources: List[EvaluatedSource]) -> float:
        if not sources:
            return 0.0

        scores = [
            safe_float(s.get("credibility_score"), 0.5) for s in sources
        ]
        return sum(scores) / len(scores)

    @staticmethod
    def calculate_average_quality(sources: List[EvaluatedSource]) -> float:
        if not sources:
            return 0.0

        scores = [
            safe_float(s.get("quality_score"), 0.5) for s in sources
        ]
        return sum(scores) / len(scores)

    def calculate_confidence(
            self,
            sources: List[EvaluatedSource],
            consensus: str,
    ) -> float:
        if not sources:
            return 0.3

        avg_cred = self.calculate_overall_credibility(sources)
        avg_quality = self.calculate_average_quality(sources)

        stance_counts = {"supports": 0, "refutes": 0}
        for source in sources:
            stance = source.get("stance", "unclear")
            if stance in stance_counts:
                stance_counts[stance] += 1

        total_decisive = stance_counts["supports"] + stance_counts["refutes"]

        if total_decisive == 0:
            return 0.3

        majority = max(stance_counts.values())
        agreement_ratio = majority / total_decisive

        base_confidence = (avg_cred * 0.4 + avg_quality * 0.3 + agreement_ratio * 0.3)

        if consensus in {"strong_support", "strong_refutation"}:
            return min(0.95, base_confidence * 1.2)
        elif consensus in {"likely_true", "likely_false"}:
            return min(0.85, base_confidence * 1.1)
        elif consensus == "mixed":
            return min(0.6, base_confidence * 0.9)
        else:
            return min(0.5, base_confidence * 0.8)


def score_recency(published_date: Optional[str]) -> float:
    scorer = RecencyScorer()
    return scorer.score(published_date)


def score_fit(claim: str, evidence: dict) -> float:
    scorer = FitScorer()
    return scorer.score(claim, evidence)


def calculate_overall_credibility(sources: List[EvaluatedSource]) -> float:
    scorer = AggregationScorer()
    return scorer.calculate_overall_credibility(sources)


def calculate_average_quality(sources: List[EvaluatedSource]) -> float:
    scorer = AggregationScorer()
    return scorer.calculate_average_quality(sources)


def calculate_confidence(sources: List[EvaluatedSource], consensus: str) -> float:
    scorer = AggregationScorer()
    return scorer.calculate_confidence(sources, consensus)


def create_empty_evaluation() -> EvaluationResult:
    return {
        "claim_id": "unknown",
        "retrieval_status": "no_evidence",
        "avg_evidence_fit": 0.0,
        "overall_credibility": 0.0,
        "evidence_quality": 0.0,
        "consensus_level": "insufficient",
        "evaluated_sources": [],
        "confidence": 0.0,
        "reasoning": "No evidence sources were provided for evaluation.",
    }