"""Main Evidence Evaluation Agent - Final Fix."""
import re
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import structlog

from news_fact_checker.config import EvidenceConfig, DEFAULT_EVIDENCE_CONFIG
from news_fact_checker.evidence.consensus_detector import ConsensusDetector
from news_fact_checker.evidence.credibility_scorer import CredibilityScorer
from news_fact_checker.evidence.quality_assessor import QualityAssessor, assess_evidence_quality
from news_fact_checker.evidence.reasoning_generator import ReasoningGenerator, generate_reasoning
from news_fact_checker.evidence.stance_classifier import deterministic_stance_classification, StanceResult


def _assess_recency(published_date: Optional[str] = None) -> float:
    if not published_date:
        return 0.7
    try:
        ds = published_date.strip()
        if len(ds) == 10:
            dt = datetime.fromisoformat(ds).replace(tzinfo=timezone.utc)
        else:
            ds = ds.replace("Z", "+00:00")
            dt = datetime.fromisoformat(ds)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        age_days = max(0.0, (now - dt).total_seconds() / 86400.0)

        if age_days <= 30: return 1.0
        if age_days <= 365: return max(0.6, 1.0 - (age_days - 30) / 600.0)
        return 0.4
    except Exception:
        return 0.7


def _evidence_fit(claim: str, evidence: Dict[str, Any]) -> float:
    """How well evidence matches claim (enhanced with report date validation)."""
    text = f"{evidence.get('source_title', '')} {evidence.get('snippet', '')}".lower()
    c = (claim or "").lower()

    # NEW: Report date validation
    claim_report_dates = re.findall(r"report from (\w+ \d{4})", c)
    if claim_report_dates:
        pub_date = evidence.get("published_date", "")
        for report_date in claim_report_dates:
            if report_date.lower() not in text and report_date.lower() not in pub_date.lower():
                return 0.15  # Severe penalty for wrong report date

    # Existing numeric/year/keyword matching
    claim_nums = re.findall(r"\b\d+(?:\.\d+)?\b", c)
    ev_nums = set(re.findall(r"\b\d+(?:\.\d+)?\b", text))
    num_match = 1.0
    if claim_nums:
        hits = sum(1 for n in claim_nums if n in ev_nums)
        num_match = hits / len(claim_nums)

    claim_years = set(re.findall(r"\b(19\d{2}|20\d{2})\b", c))
    ev_years = set(re.findall(r"\b(19\d{2}|20\d{2})\b", text))
    year_match = 1.0
    if claim_years:
        year_match = 1.0 if (claim_years & ev_years) else 0.4

    claim_keywords = set([w for w in re.findall(r"[a-z]{3,}", c)])
    ev_keywords = set(re.findall(r"[a-z]{3,}", text))
    kw_overlap = len(claim_keywords & ev_keywords) / len(claim_keywords) if claim_keywords else 0.0

    fit = (0.50 * num_match) + (0.25 * year_match) + (0.25 * kw_overlap)
    return float(max(0.0, min(1.0, fit)))


def _calculate_overall_credibility(sources: List[Dict]) -> float:
    """Calculate weighted average credibility across all sources."""
    if not sources:
        return 0.0

    total_weight = sum(
        s.get('relevance_score', 1.0) *
        s.get('evidence_fit', 1.0) *
        s.get('recency_score', 1.0)
        for s in sources
    )

    if total_weight == 0:
        return sum(s['credibility_score'] for s in sources) / len(sources)

    weighted_sum = sum(
        s['credibility_score'] *
        s.get('relevance_score', 1.0) *
        s.get('evidence_fit', 1.0) *
        s.get('recency_score', 1.0)
        for s in sources
    )
    return weighted_sum / total_weight


def _calculate_average_quality(sources: List[Dict]) -> float:
    """Calculate average evidence quality across all sources."""
    if not sources:
        return 0.0
    return sum(s['quality_score'] for s in sources) / len(sources)


def _calculate_confidence(sources: List[Dict], consensus: str) -> float:
    """Enhanced confidence calculation."""
    if not sources:
        return 0.0

    if len(sources) < 2:
        return 0.35

    source_factor = min(len(sources) / 5.0, 1.0)

    consensus_scores = {
        "strong_support": 0.90,
        "strong_refutation": 0.90,
        "likely_true": 0.70,
        "likely_false": 0.70,
        "mixed": 0.40,
        "insufficient": 0.25,
    }
    consensus_factor = consensus_scores.get(consensus, 0.30)

    avg_cred = sum(s.get("credibility_score", 0.5) for s in sources) / len(sources)
    avg_fit = sum(s.get("evidence_fit", 1.0) for s in sources) / len(sources)
    max_fit = max(s.get("evidence_fit", 1.0) for s in sources)
    avg_quality = sum(s.get("quality_score", 0.5) for s in sources) / len(sources)

    base = (
        0.25 * source_factor +
        0.40 * consensus_factor +
        0.15 * avg_cred +
        0.10 * avg_fit +
        0.10 * avg_quality
    )

    # Cap based on fit
    if max_fit < 0.30:
        base = min(base, 0.40)
    elif max_fit < 0.50:
        base = min(base, 0.65)
    elif max_fit < 0.70:
        base = min(base, 0.80)

    return float(max(0.0, min(1.0, base)))


def _empty_evaluation() -> Dict[str, Any]:
    """Return default evaluation when no evidence is provided."""
    return {
        "claim_id": "unknown",
        "retrieval_status": "no_evidence",
        "avg_evidence_fit": 0.0,
        "overall_credibility": 0.0,
        "evidence_quality": 0.0,
        "consensus_level": "insufficient",
        "evaluated_sources": [],
        "confidence": 0.0,
        "reasoning": "No evidence sources available for evaluation."
    }


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
            return _empty_evaluation()

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

            overall_cred = _calculate_overall_credibility(evaluated_sources)
            avg_quality = _calculate_average_quality(evaluated_sources)

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
        overall_cred = _calculate_overall_credibility(evaluated_sources)
        avg_quality = _calculate_average_quality(evaluated_sources)
        confidence = _calculate_confidence(evaluated_sources, consensus)

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
        recency_score = _assess_recency(evidence.get("published_date"))
        fit_score = _evidence_fit(claim, evidence)

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