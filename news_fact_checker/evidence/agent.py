from __future__ import annotations

from typing import List, Optional
import structlog

from news_fact_checker.evidence.config import EvidenceConfig, DEFAULT_EVIDENCE_CONFIG
from news_fact_checker.evidence.models import EvaluatedSource, EvaluationResult, EvidenceSource
from news_fact_checker.evidence.credibility_scorer import CredibilityScorer
from news_fact_checker.evidence.quality_assessor import QualityAssessor
from news_fact_checker.evidence.consensus_detector import ConsensusDetector
from news_fact_checker.evidence.reasoning_generator import ReasoningGenerator
from news_fact_checker.evidence.stance_classifier import StanceClassifier
from news_fact_checker.evidence.scoring import (
    score_recency,
    score_fit,
    calculate_overall_credibility,
    calculate_average_quality,
    calculate_confidence,
    create_empty_evaluation,
)
from news_fact_checker.evidence.constants import (
    WEAK_FIT_THRESHOLD,
    STRONG_FIT_DOWNGRADE_THRESHOLD,
    IMPLICIT_REFUTATION_CONFIDENCE_BASE,
    IMPLICIT_REFUTATION_CONFIDENCE_MULTIPLIER,
    IMPLICIT_REFUTATION_CONFIDENCE_CAP,
)


class ImplicitRefutationDetector:

    @staticmethod
    def detect(evaluated_sources: List[EvaluatedSource]) -> bool:
        if not evaluated_sources:
            return False

        avg_fit = sum(
            s.get("evidence_fit", 1.0) for s in evaluated_sources
        ) / len(evaluated_sources)

        return avg_fit < WEAK_FIT_THRESHOLD

    @staticmethod
    def create_evaluation(
            evaluated_sources: List[EvaluatedSource],
            claim_id: str,
    ) -> EvaluationResult:
        avg_fit = sum(
            s.get("evidence_fit", 1.0) for s in evaluated_sources
        ) / len(evaluated_sources)

        confidence = min(
            IMPLICIT_REFUTATION_CONFIDENCE_CAP,
            IMPLICIT_REFUTATION_CONFIDENCE_BASE + (1.0 - avg_fit) * IMPLICIT_REFUTATION_CONFIDENCE_MULTIPLIER
        )

        overall_cred = calculate_overall_credibility(evaluated_sources)
        avg_quality = calculate_average_quality(evaluated_sources)

        reasoning = (
            f"The available evidence does not adequately support this claim. "
            f"With an average evidence fit of {avg_fit:.0%}, sources either reference "
            f"different time periods, different metrics, or conflicting data. "
            f"This suggests the claim as stated is likely inaccurate."
        )

        return {
            "claim_id": claim_id,
            "retrieval_status": "weak_fit",
            "avg_evidence_fit": round(avg_fit, 3),
            "overall_credibility": round(overall_cred, 3),
            "evidence_quality": round(avg_quality, 3),
            "consensus_level": "likely_false",
            "evaluated_sources": evaluated_sources,
            "confidence": round(confidence, 3),
            "reasoning": reasoning,
        }


class SourceEvaluator:

    def __init__(
            self,
            credibility_scorer: CredibilityScorer,
            quality_assessor: QualityAssessor,
            stance_classifier: StanceClassifier,
            config: EvidenceConfig,
    ):
        self.credibility_scorer = credibility_scorer
        self.quality_assessor = quality_assessor
        self.stance_classifier = stance_classifier
        self.config = config
        self.logger = structlog.get_logger().bind(component="source_evaluator")

    def evaluate(self, claim: str, evidence: EvidenceSource) -> EvaluatedSource:
        try:
            stance_result = self.stance_classifier.classify(
                claim_text=claim,
                snippet=evidence.get("snippet", ""),
                source_url=evidence.get("source_url", ""),
                source_title=evidence.get("source_title", ""),
            )
            stance_label = stance_result.label
            stance_confidence = stance_result.confidence
        except Exception as e:
            self.logger.warning(
                "stance_classification_failed",
                error=str(e),
                source_url=evidence.get("source_url", ""),
            )
            stance_label = "unclear"
            stance_confidence = 0.5

        domain_score = self.credibility_scorer.score_domain(evidence["source_url"])

        quality_score = self.quality_assessor.assess(
            claim,
            evidence.get("snippet", ""),
            stance_label,
        )

        recency_score = score_recency(evidence.get("published_date"))
        fit_score = score_fit(claim, evidence)

        final_score = (
                domain_score * self.config.domain_weight
                + quality_score * self.config.quality_weight
                + recency_score * self.config.recency_weight
        )

        evaluated: EvaluatedSource = {
            **evidence,
            "stance": stance_label,
            "stance_confidence": round(stance_confidence, 3),
            "credibility_score": round(domain_score, 3),
            "quality_score": round(quality_score, 3),
            "recency_score": round(recency_score, 3),
            "evidence_fit": round(fit_score, 3),
            "final_score": round(final_score, 3),
            "credibility_tier": self.credibility_scorer.get_tier(evidence["source_url"]),
        }

        return evaluated


class EvidenceEvaluationAgent:

    def __init__(self, config: Optional[EvidenceConfig] = None):
        self.config = config or DEFAULT_EVIDENCE_CONFIG
        self.logger = structlog.get_logger().bind(component="evidence_agent")

        self.credibility_scorer = CredibilityScorer(self.config)
        self.quality_assessor = QualityAssessor()
        self.stance_classifier = StanceClassifier()
        self.consensus_detector = ConsensusDetector(self.config)
        self.reasoning_generator = ReasoningGenerator()

        self.source_evaluator = SourceEvaluator(
            self.credibility_scorer,
            self.quality_assessor,
            self.stance_classifier,
            self.config,
        )

        self.implicit_refutation_detector = ImplicitRefutationDetector()

    def evaluate(
            self,
            claim: str,
            evidence_list: List[EvidenceSource],
    ) -> EvaluationResult:
        if not evidence_list:
            self.logger.warning("empty_evidence_list", claim=claim[:100])
            return create_empty_evaluation()

        self.logger.info(
            "evaluation_started",
            claim=claim[:100],
            num_sources=len(evidence_list),
        )

        evaluated_sources = [
            self.source_evaluator.evaluate(claim, evidence)
            for evidence in evidence_list
        ]

        if self.implicit_refutation_detector.detect(evaluated_sources):
            result = self.implicit_refutation_detector.create_evaluation(
                evaluated_sources,
                evidence_list[0].get("claim_id", "unknown"),
            )

            self.logger.info(
                "implicit_refutation_triggered",
                claim_id=result["claim_id"],
                avg_fit=result["avg_evidence_fit"],
            )

            return result

        consensus = self.consensus_detector.detect(evaluated_sources, claim)

        max_fit = max(
            s.get("evidence_fit", 1.0) for s in evaluated_sources
        ) if evaluated_sources else 0.0

        if consensus in {"strong_support", "strong_refutation"} and max_fit < STRONG_FIT_DOWNGRADE_THRESHOLD:
            consensus = "likely_true" if consensus == "strong_support" else "likely_false"
            self.logger.info(
                "consensus_downgraded",
                reason="weak_evidence_fit",
                max_fit=max_fit,
            )

        overall_cred = calculate_overall_credibility(evaluated_sources)
        avg_quality = calculate_average_quality(evaluated_sources)
        confidence = calculate_confidence(evaluated_sources, consensus)

        reasoning = self.reasoning_generator.generate(
            claim,
            evaluated_sources,
            consensus,
            confidence,
        )

        avg_fit = sum(
            s.get("evidence_fit", 1.0) for s in evaluated_sources
        ) / len(evaluated_sources)

        retrieval_status = "ok" if avg_fit >= WEAK_FIT_THRESHOLD else "weak_fit"

        result: EvaluationResult = {
            "claim_id": evidence_list[0].get("claim_id", "unknown"),
            "retrieval_status": retrieval_status,
            "avg_evidence_fit": round(avg_fit, 3),
            "overall_credibility": round(overall_cred, 3),
            "evidence_quality": round(avg_quality, 3),
            "consensus_level": consensus,
            "evaluated_sources": evaluated_sources,
            "confidence": round(confidence, 3),
            "reasoning": reasoning,
        }

        self.logger.info(
            "evaluation_completed",
            claim_id=result["claim_id"],
            consensus=consensus,
            credibility=overall_cred,
            confidence=confidence,
            avg_fit=avg_fit,
        )

        return result

    def batch_evaluate(
            self,
            claims_with_evidence: List[dict],
    ) -> List[EvaluationResult]:
        results = []
        for item in claims_with_evidence:
            result = self.evaluate(
                claim=item["claim"],
                evidence_list=item["evidence"],
            )
            results.append(result)

        self.logger.info("batch_evaluation_completed", total=len(results))
        return results