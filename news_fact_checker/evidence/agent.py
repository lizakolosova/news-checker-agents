"""Main Evidence Evaluation Agent - Final Fix."""
from news_fact_checker.research.scoring import evidence_fit, assess_recency, empty_evaluation, calculate_overall_credibility, calculate_average_quality, calculate_confidence
from typing import List, Optional, Dict, Any

import structlog

from news_fact_checker.config import EvidenceConfig, DEFAULT_EVIDENCE_CONFIG
from news_fact_checker.evidence.consensus_detector import ConsensusDetector
from news_fact_checker.evidence.credibility_scorer import CredibilityScorer
from news_fact_checker.evidence.quality_assessor import QualityAssessor, assess_evidence_quality
from news_fact_checker.evidence.reasoning_generator import ReasoningGenerator, generate_reasoning
from news_fact_checker.evidence.stance_classifier import deterministic_stance_classification, StanceResult

class EvidenceEvaluationAgent:
    """Evidence Evaluation Agent with implicit refutation for poor fits."""

    def __init__(self, config: Optional[EvidenceConfig] = None):
        self.config = config or DEFAULT_EVIDENCE_CONFIG
        self.logger = structlog.get_logger().bind(component="evidenceagent")

        self.has_groq = False
        self.groq_client = None

        self.logger.info(
            "llm_disabled",
            reason="Running without paid LLM provider (Groq removed)."
        )

        self.credibility_scorer = CredibilityScorer(self.config)
        self.quality_assessor = QualityAssessor()
        self.reasoning_generator = ReasoningGenerator(self.logger)
        self.consensus_detector = ConsensusDetector()

    def evaluate_evidence(
        self,
        claim: str,
        evidence_list: List[Dict]
    ) -> Dict[str, Any]:
        """
        Main evaluation pipeline with implicit refutation for poor evidence fits.
        """
        if not evidence_list:
            self.logger.warning("empty_evidence_list", claim=claim[:100])
            return empty_evaluation()

        self.logger.info(
            "evaluation_started",
            claim=claim[:100],
            num_sources=len(evidence_list)
        )

        # Step 1: Evaluate each source
        evaluated_sources = []
        for evidence in evidence_list:
            evaluated = self._evaluate_single_source(claim, evidence)
            evaluated_sources.append(evaluated)

        avg_fit = sum(
            s.get("evidence_fit", 1.0) for s in evaluated_sources
        ) / len(evaluated_sources) if evaluated_sources else 0.0

        if avg_fit < 0.35:
            self.logger.info(
                "implicit_refutation_triggered",
                avg_fit=avg_fit,
                reason="evidence_does_not_match_claim"
            )

            consensus = "likely_false"
            confidence = min(0.75, 0.5 + (1.0 - avg_fit) * 0.5)

            overall_cred = calculate_overall_credibility(evaluated_sources)
            avg_quality = calculate_average_quality(evaluated_sources)

            # Generate special reasoning for poor fit
            reasoning = (
                f"The available evidence does not adequately support this claim. "
                f"With an average evidence fit of {avg_fit:.0%}, sources either reference "
                f"different time periods, different metrics, or conflicting data. "
                f"This suggests the claim as stated is likely inaccurate."
            )

            result = {
                "claim_id": evidence_list[0].get('claim_id', 'unknown'),
                "retrieval_status": "weak_fit",
                "avg_evidence_fit": round(avg_fit, 3),
                "overall_credibility": round(overall_cred, 3),
                "evidence_quality": round(avg_quality, 3),
                "consensus_level": consensus,
                "evaluated_sources": evaluated_sources,
                "confidence": round(confidence, 3),
                "reasoning": reasoning
            }

            self.logger.info(
                "evaluation_completed_implicit_refutation",
                claim_id=result['claim_id'],
                avg_fit=avg_fit,
                confidence=confidence
            )

            return result

        # Step 3: Normal consensus detection
        consensus = self.consensus_detector.detect_consensus(
            evaluated_sources,
            claim=claim
        )

        # Step 4: Downgrade strong consensus if fit is weak
        max_fit = max(
            s.get("evidence_fit", 1.0) for s in evaluated_sources
        ) if evaluated_sources else 0.0

        if consensus in {"strong_support", "strong_refutation"} and max_fit < 0.65:
            consensus = "likely_true" if consensus == "strong_support" else "likely_false"
            self.logger.info("consensus_downgraded", reason="weak_evidence_fit", max_fit=max_fit)

        # Step 5: Calculate metrics
        overall_cred = calculate_overall_credibility(evaluated_sources)
        avg_quality = calculate_average_quality(evaluated_sources)
        confidence = calculate_confidence(evaluated_sources, consensus)

        # Step 6: Generate reasoning
        if self.reasoning_generator:
            reasoning = generate_reasoning(
                claim,
                evaluated_sources,
                consensus
            )
        else:
            reasoning = (
                f"Consensus: {consensus}. "
                f"Based on {len(evaluated_sources)} sources. "
                f"LLM-based reasoning unavailable in heuristic mode."
            )

        retrieval_status = "ok" if avg_fit >= 0.35 else "weak_fit"

        result = {
            "claim_id": evidence_list[0].get('claim_id', 'unknown'),
            "retrieval_status": retrieval_status,
            "avg_evidence_fit": round(avg_fit, 3),
            "overall_credibility": round(overall_cred, 3),
            "evidence_quality": round(avg_quality, 3),
            "consensus_level": consensus,
            "evaluated_sources": evaluated_sources,
            "confidence": round(confidence, 3),
            "reasoning": reasoning
        }

        self.logger.info(
            "evaluation_completed",
            claim_id=result['claim_id'],
            consensus=consensus,
            credibility=overall_cred,
            confidence=confidence,
            avg_fit=avg_fit
        )

        return result

    def _evaluate_single_source(self, claim: str, evidence: Dict) -> Dict:
        """Evaluate a single evidence source.

        Responsibilities here:
        - Classify stance (supports / refutes / unclear)
        - Score domain credibility, quality, recency, and fit
        """

        # 1) Stance classification (done here, not in ResearchAgent)
        try:
            stance_res: StanceResult = deterministic_stance_classification(
                claim_text=claim,
                snippet=evidence.get("snippet", ""),
                source_url=evidence.get("source_url", ""),
                source_title=evidence.get("source_title", ""),
            )
            stance_label = stance_res.label
            stance_confidence = stance_res.confidence
        except Exception as e:
            self.logger.warning(
                "stance_classification_failed",
                error=str(e),
                source_url=evidence.get("source_url", ""),
            )
            stance_label = "unclear"
            stance_confidence = 0.5

        # 2) Domain credibility
        domain_score = self.credibility_scorer.assess_domain_credibility(
            evidence["source_url"]
        )

        # 3) Evidence quality (uses claim, snippet, stance label)
        if self.quality_assessor:
            quality_score = assess_evidence_quality(
                claim,
                evidence.get("snippet", ""),
                stance_label,
            )
        else:
            quality_score = 0.6 if stance_label in {"supports", "refutes"} else 0.4

        # 4) Recency & fit
        recency_score = assess_recency(evidence.get("published_date"))
        fit_score = evidence_fit(claim, evidence)

        # 5) Final score (same weighting logic as before)
        final_score = (
                domain_score * self.config.domain_weight
                + quality_score * self.config.quality_weight
                + recency_score * self.config.recency_weight
        )

        # 6) Return enriched evidence object
        return {
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

    def batch_evaluate(self, claims_with_evidence: List[Dict]) -> List[Dict]:
        """Evaluate multiple claims in batch."""
        results = []
        for item in claims_with_evidence:
            result = self.evaluate_evidence(
                claim=item['claim'],
                evidence_list=item['evidence']
            )
            results.append(result)

        self.logger.info("batch_evaluation_completed", total=len(results))
        return results