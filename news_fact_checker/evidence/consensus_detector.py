"""Consensus detection for evidence evaluation."""

from __future__ import annotations

from typing import List, Dict, Tuple
import structlog

from news_fact_checker.evidence.models import ConsensusMetrics, EvaluatedSource
from news_fact_checker.evidence.config import EvidenceConfig, DEFAULT_EVIDENCE_CONFIG
from news_fact_checker.evidence.utils import (
    safe_float,
    extract_years,
    extract_months,
    looks_like_attribution_claim,
    extract_attribution_entities,
)
from news_fact_checker.evidence.constants import (
    MIN_TOTAL_WEIGHT,
    TEMPORAL_PENALTY_YEAR_MISMATCH,
    TEMPORAL_PENALTY_MONTH_MISMATCH,
    AUTHORITY_PENALTY_DEFAULT,
    AUTHORITY_PENALTY_GOVERNMENT,
)

logger = structlog.get_logger().bind(component="consensus_detector")


class TemporalAnalyzer:

    @staticmethod
    def calculate_penalty(claim: str, text: str) -> Tuple[float, str]:
        claim_years = extract_years(claim)
        ev_years = extract_years(text)

        if claim_years and ev_years and claim_years.isdisjoint(ev_years):
            return TEMPORAL_PENALTY_YEAR_MISMATCH, "year_mismatch"

        claim_months = extract_months(claim)
        ev_months = extract_months(text)

        if claim_months and ev_months and claim_months.isdisjoint(ev_months):
            return TEMPORAL_PENALTY_MONTH_MISMATCH, "month_mismatch"

        return 1.0, "ok"


class AuthorityAnalyzer:

    @staticmethod
    def calculate_penalty(
            claim: str,
            source_url: str,
            source_title: str,
            snippet: str,
    ) -> float:
        if not looks_like_attribution_claim(claim):
            return 1.0

        entities = extract_attribution_entities(claim)
        if not entities:
            return 1.0

        haystack = f"{source_url} {source_title} {snippet}".lower()

        for entity in entities:
            if entity.lower() in haystack:
                return 1.0

        url_lower = (source_url or "").lower()
        if any(
                tld in url_lower
                for tld in (".gov", ".int", ".europa.eu", ".eu", ".ac.", ".edu")
        ):
            return AUTHORITY_PENALTY_GOVERNMENT

        return AUTHORITY_PENALTY_DEFAULT


class WeightCalculator:

    def __init__(self):
        self.temporal_analyzer = TemporalAnalyzer()
        self.authority_analyzer = AuthorityAnalyzer()

    def calculate_weighted_stances(
            self,
            claim: str,
            sources: List[EvaluatedSource],
    ) -> Tuple[float, float, float, Dict[str, int]]:
        weighted_support = 0.0
        weighted_refute = 0.0
        total_weight = 0.0

        debug_counts = {
            "year_mismatch": 0,
            "month_mismatch": 0,
            "authority_penalized": 0,
        }

        for source in sources:
            stance = source.get("stance", "unclear")
            if stance not in {"supports", "refutes"}:
                continue

            base_weight = self._calculate_base_weight(source)

            text = f"{source.get('source_title', '')} {source.get('snippet', '')}"
            temporal_penalty, t_reason = self.temporal_analyzer.calculate_penalty(
                claim, text
            )

            if t_reason == "year_mismatch":
                debug_counts["year_mismatch"] += 1
            elif t_reason == "month_mismatch":
                debug_counts["month_mismatch"] += 1

            authority_penalty = self.authority_analyzer.calculate_penalty(
                claim=claim,
                source_url=source.get("source_url", "") or "",
                source_title=source.get("source_title", "") or "",
                snippet=source.get("snippet", "") or "",
            )

            if authority_penalty < 1.0:
                debug_counts["authority_penalized"] += 1

            weight = base_weight * temporal_penalty * authority_penalty

            if stance == "supports":
                weighted_support += weight
            else:
                weighted_refute += weight

            total_weight += weight

        return weighted_support, weighted_refute, total_weight, debug_counts

    @staticmethod
    def _calculate_base_weight(source: EvaluatedSource) -> float:
        credibility = safe_float(source.get("credibility_score"), 0.5)
        relevance = safe_float(source.get("relevance_score"), 0.05)
        quality = safe_float(source.get("quality_score"), 0.5)
        fit = safe_float(source.get("evidence_fit"), 0.6)
        recency = safe_float(source.get("recency_score"), 0.7)
        stance_conf = safe_float(source.get("stance_confidence"), 0.6)

        return credibility * relevance * quality * fit * recency * stance_conf


class ConsensusClassifier:

    @staticmethod
    def classify(
            support_ratio: float,
            refute_ratio: float,
            strong_threshold: float,
            likely_threshold: float,
            mixed_threshold: float,
    ) -> str:
        if support_ratio >= strong_threshold:
            return "strong_support"
        if refute_ratio >= strong_threshold:
            return "strong_refutation"

        if support_ratio >= likely_threshold:
            return "likely_true"
        if refute_ratio >= likely_threshold:
            return "likely_false"

        if support_ratio >= mixed_threshold and refute_ratio >= mixed_threshold:
            return "mixed"

        return "insufficient"


class ConsensusDetector:

    def __init__(self, config: EvidenceConfig = None):
        self.config = config or DEFAULT_EVIDENCE_CONFIG
        self.weight_calculator = WeightCalculator()
        self.classifier = ConsensusClassifier()

    def detect(
            self,
            evaluated_sources: List[EvaluatedSource],
            claim: str = "",
    ) -> str:
        if not evaluated_sources:
            return "insufficient"

        (
            weighted_support,
            weighted_refute,
            total_weight,
            debug_counts,
        ) = self.weight_calculator.calculate_weighted_stances(claim, evaluated_sources)

        if total_weight < MIN_TOTAL_WEIGHT:
            logger.info(
                "insufficient_weighted_evidence",
                total_weight=round(total_weight, 3),
            )
            return "insufficient"

        support_ratio = weighted_support / total_weight if total_weight else 0.0
        refute_ratio = weighted_refute / total_weight if total_weight else 0.0

        consensus = self.classifier.classify(
            support_ratio=support_ratio,
            refute_ratio=refute_ratio,
            strong_threshold=self.config.strong_consensus_threshold,
            likely_threshold=self.config.likely_consensus_threshold,
            mixed_threshold=self.config.mixed_consensus_threshold,
        )

        logger.info(
            "consensus_detected",
            consensus=consensus,
            support_ratio=round(support_ratio, 3),
            refute_ratio=round(refute_ratio, 3),
            total_weight=round(total_weight, 3),
            num_sources=len(evaluated_sources),
            **debug_counts,
        )

        return consensus

    def detect_with_metrics(
            self,
            evaluated_sources: List[EvaluatedSource],
            claim: str = "",
    ) -> Tuple[str, ConsensusMetrics]:
        consensus = self.detect(evaluated_sources, claim)

        (
            weighted_support,
            weighted_refute,
            total_weight,
            debug_counts,
        ) = self.weight_calculator.calculate_weighted_stances(claim, evaluated_sources)

        support_ratio = weighted_support / total_weight if total_weight else 0.0
        refute_ratio = weighted_refute / total_weight if total_weight else 0.0

        metrics = ConsensusMetrics(
            support_ratio=support_ratio,
            refute_ratio=refute_ratio,
            total_weight=total_weight,
            num_sources=len(evaluated_sources),
            debug_counts=debug_counts,
        )

        return consensus, metrics