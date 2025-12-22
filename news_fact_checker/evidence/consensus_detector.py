"""Consensus detection across multiple evidence sources."""

from __future__ import annotations

import re
import structlog
from typing import List, Dict, Tuple, Set


def _safe_float(x, default: float) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _extract_years(text: str) -> Set[str]:
    return set(re.findall(r"\b(19\d{2}|20\d{2})\b", text or ""))


def _extract_months(text: str) -> Set[str]:
    months = {
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december",
    }
    tokens = set(re.findall(r"[a-z]+", (text or "").lower()))
    return tokens.intersection(months)


def _looks_like_attribution_claim(claim: str) -> bool:
    c = (claim or "").lower()
    return any(p in c for p in ("according to", "said", "stated", "reports", "reported", "announced", "data from"))


def _extract_attribution_entities(claim: str) -> List[str]:
    """
    Very lightweight attribution-entity extraction.
    We look for the phrase after 'according to' up to punctuation.
    This is intentionally heuristic (generic; no NER dependency).
    """
    c = (claim or "").strip()
    m = re.search(r"(?i)\baccording to\s+([^.,;:]+)", c)
    if not m:
        return []
    ent = m.group(1).strip()
    ent = re.sub(r"(?i)^(the|a|an)\s+", "", ent).strip()
    words = ent.split()
    ent = " ".join(words[:8]).strip()
    return [ent] if ent else []


def _authority_penalty(claim: str, source_url: str, source_title: str, snippet: str) -> float:
    """
    If the claim is attributed ("according to X"), reduce weight for sources
    that don't appear to match X.

    This is generic: it uses the attribution entity found in the claim.
    """
    if not _looks_like_attribution_claim(claim):
        return 1.0

    ents = _extract_attribution_entities(claim)
    if not ents:
        return 1.0

    hay = f"{source_url} {source_title} {snippet}".lower()
    for ent in ents:
        if ent.lower() in hay:
            return 1.0

    url = (source_url or "").lower()
    if any(tld in url for tld in (".gov", ".int", ".europa.eu", ".eu", ".ac.", ".edu")):
        return 0.75

    return 0.40


def _temporal_penalty(claim: str, text: str) -> Tuple[float, str]:
    """
    Hard temporal grounding:
    - If claim specifies a year and evidence specifies a different year -> strong penalty.
    - If claim specifies a month and evidence specifies a different month -> moderate penalty.
    Returns (penalty_multiplier, reason)
    """
    claim_years = _extract_years(claim)
    ev_years = _extract_years(text)

    if claim_years and ev_years and claim_years.isdisjoint(ev_years):
        return 0.10, "year_mismatch"  # near-zero weight

    claim_months = _extract_months(claim)
    ev_months = _extract_months(text)

    if claim_months and ev_months and claim_months.isdisjoint(ev_months):
        return 0.35, "month_mismatch"  # downweight heavily

    return 1.0, "ok"


def _calculate_weighted_stances(claim: str, sources: List[Dict]) -> Tuple[float, float, float, Dict[str, int]]:
    """
    Calculate weighted support and refutation.

    Base weight = credibility_score * relevance_score * quality_score
                  * evidence_fit * recency_score * stance_confidence

    Then apply:
      - temporal penalty (year/month mismatch)
      - attribution authority penalty ("according to X")

    Notes:
    - Only supports/refutes contribute to total_weight (denominator).
    - 'unclear' does not dilute the denominator.
    """
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

        cred = _safe_float(source.get("credibility_score"), 0.5)
        rel = _safe_float(source.get("relevance_score"), 0.05)
        qual = _safe_float(source.get("quality_score"), 0.5)
        fit = _safe_float(source.get("evidence_fit"), 0.6)
        rec = _safe_float(source.get("recency_score"), 0.7)
        scf = _safe_float(source.get("stance_confidence"), 0.6)

        base_weight = cred * rel * qual * fit * rec * scf

        text = f"{source.get('source_title','')} {source.get('snippet','')}"
        t_pen, t_reason = _temporal_penalty(claim, text)
        if t_reason == "year_mismatch":
            debug_counts["year_mismatch"] += 1
        elif t_reason == "month_mismatch":
            debug_counts["month_mismatch"] += 1

        # Attribution authority grounding
        a_pen = _authority_penalty(
            claim=claim,
            source_url=source.get("source_url", "") or "",
            source_title=source.get("source_title", "") or "",
            snippet=source.get("snippet", "") or "",
        )
        if a_pen < 1.0:
            debug_counts["authority_penalized"] += 1

        weight = base_weight * t_pen * a_pen

        if stance == "supports":
            weighted_support += weight
            total_weight += weight
        else:
            weighted_refute += weight
            total_weight += weight

    return weighted_support, weighted_refute, total_weight, debug_counts


def _classify_consensus(
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
    """Detects consensus level across multiple evidence sources via weighted voting."""

    STRONG_THRESHOLD = 0.75
    LIKELY_THRESHOLD = 0.60
    MIXED_THRESHOLD = 0.20

    MIN_TOTAL_WEIGHT = 0.03

    def __init__(self):
        self.logger = structlog.get_logger().bind(component="consensus_detector")

    def detect_consensus(
        self,
        evaluated_sources: List[Dict],
        claim: str = "",
        strong_threshold: float = STRONG_THRESHOLD,
        likely_threshold: float = LIKELY_THRESHOLD,
        mixed_threshold: float = MIXED_THRESHOLD,
    ) -> str:
        if not evaluated_sources:
            return "insufficient"

        weighted_support, weighted_refute, total_weight, debug_counts = _calculate_weighted_stances(
            claim=claim,
            sources=evaluated_sources,
        )

        if total_weight < self.MIN_TOTAL_WEIGHT:
            self.logger.info("insufficient_weighted_evidence", total_weight=round(total_weight, 3))
            return "insufficient"

        support_ratio = weighted_support / total_weight if total_weight else 0.0
        refute_ratio = weighted_refute / total_weight if total_weight else 0.0

        consensus = _classify_consensus(
            support_ratio=support_ratio,
            refute_ratio=refute_ratio,
            strong_threshold=strong_threshold,
            likely_threshold=likely_threshold,
            mixed_threshold=mixed_threshold,
        )

        self.logger.info(
            "consensus_detected",
            consensus=consensus,
            support_ratio=round(support_ratio, 3),
            refute_ratio=round(refute_ratio, 3),
            total_weight=round(total_weight, 3),
            num_sources=len(evaluated_sources),
            **debug_counts,
        )

        return consensus
