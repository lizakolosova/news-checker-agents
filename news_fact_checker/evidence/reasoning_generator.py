from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Dict, Optional


def _normalize_confidence(confidence: Any) -> int:
    """
    Normalize confidence to 0-100 integer.

    Args:
        confidence: Can be float (0-1 or 0-100), int, or string

    Returns:
        int: Confidence as percentage (0-100)
    """
    try:
        value = float(confidence)
        if 0.0 <= value <= 100.0:
            return int(round(value))
        if 0.0 <= value <= 1.0:
            return int(round(value * 100))

    except (TypeError, ValueError):
        pass
    return 50


def _get_consensus_description(consensus: str) -> str:
    """Get human-readable description of consensus level."""
    descriptions = {
        "strong_support": "strongly supported by credible sources",
        "strong_refutation": "clearly contradicted by evidence",
        "likely_true": "likely accurate based on available evidence",
        "likely_false": "likely inaccurate based on available evidence",
        "mixed": "evidence shows conflicting information",
        "insufficient": "insufficient evidence to determine accuracy",
    }
    return descriptions.get(consensus, "unclear evidence")


def _count_sources_by_stance(sources: List[Dict]) -> Dict[str, int]:
    """Count sources by their stance classification."""
    counts = {"supports": 0, "refutes": 0, "unclear": 0}

    for source in sources:
        stance = source.get("stance", "unclear")
        if stance in counts:
            counts[stance] += 1

    return counts


def _get_tier_distribution(sources: List[Dict]) -> Dict[int, int]:
    """Get distribution of sources across credibility tiers."""
    tiers = {1: 0, 2: 0, 3: 0, 0: 0}

    for source in sources:
        tier = source.get("credibility_tier", 0)
        if tier in tiers:
            tiers[tier] += 1

    return tiers


def _calculate_avg_credibility(sources: List[Dict]) -> float:
    """Calculate average credibility score across sources."""
    if not sources:
        return 0.0

    total = sum(source.get("credibility_score", 0.5) for source in sources)
    return total / len(sources)


def generate_reasoning(
    claim: str,
    sources: List[Dict],
    consensus: str,
    confidence: Optional[float] = None,
) -> str:
    """
    Generate human-readable reasoning for a fact-check verdict.

    Args:
        claim: The claim being fact-checked
        sources: List of evaluated evidence sources
        consensus: Consensus level (strong_support, likely_true, etc.)
        confidence: Optional confidence score

    Returns:
        str: Human-readable explanation
    """
    if not sources:
        return (
            "No reliable evidence sources were found to evaluate this claim. "
            "Without supporting or refuting evidence, the claim cannot be verified."
        )

    num_sources = len(sources)
    stance_counts = _count_sources_by_stance(sources)
    tier_dist = _get_tier_distribution(sources)
    avg_cred = _calculate_avg_credibility(sources)

    if confidence is not None:
        conf_pct = _normalize_confidence(confidence)
    else:
        conf_pct = 50

    consensus_desc = _get_consensus_description(consensus)

    parts = [f"This claim is {consensus_desc}."]

    if tier_dist[1] > 0:
        parts.append(
            f"Analysis is based on {num_sources} source{'s' if num_sources != 1 else ''}, "
            f"including {tier_dist[1]} highly credible source{'s' if tier_dist[1] != 1 else ''} "
            f"(government, academic, or official organizations)."
        )
    else:
        parts.append(
            f"Analysis is based on {num_sources} source{'s' if num_sources != 1 else ''} "
            f"with average credibility score of {avg_cred:.0%}."
        )

    if consensus in {"mixed", "insufficient"}:
        parts.append(
            f"Evidence includes {stance_counts['supports']} supporting source{'s' if stance_counts['supports'] != 1 else ''}, "
            f"{stance_counts['refutes']} refuting source{'s' if stance_counts['refutes'] != 1 else ''}, "
            f"and {stance_counts['unclear']} with unclear stance."
        )

    if consensus == "strong_support":
        parts.append(
            "Multiple independent sources confirm the key facts in this claim."
        )
    elif consensus == "strong_refutation":
        parts.append(
            "Multiple sources directly contradict the central facts of this claim."
        )
    elif consensus == "likely_true":
        parts.append(
            "While not definitively proven, the preponderance of evidence supports this claim."
        )
    elif consensus == "likely_false":
        parts.append(
            "While not definitively disproven, the preponderance of evidence contradicts this claim."
        )
    elif consensus == "mixed":
        parts.append(
            "Different credible sources provide conflicting information, "
            "suggesting the claim may be partially accurate or context-dependent."
        )
    elif consensus == "insufficient":
        parts.append(
            "Available evidence is too limited or unclear to make a determination."
        )

    if conf_pct >= 80:
        parts.append(f"Confidence in this assessment is high ({conf_pct}%).")
    elif conf_pct >= 60:
        parts.append(f"Confidence in this assessment is moderate ({conf_pct}%).")
    else:
        parts.append(f"Confidence in this assessment is low ({conf_pct}%).")

    return " ".join(parts)


@dataclass
class ReasoningGenerator:
    logger: Any = None

    def __init__(self, logger: Any = None):
        self.logger = logger

    def generate( self,  claim: str,  sources: List[Dict],consensus: str,confidence: Optional[float] = None,) -> str:
        """
        Generate reasoning explanation.

        This is a convenience wrapper around the module-level function.

        Args:
            claim: The claim being evaluated
            sources: Evaluated evidence sources
            consensus: Consensus level
            confidence: Optional confidence score

        Returns:
            str: Human-readable explanation
        """
        return generate_reasoning(claim, sources, consensus, confidence)