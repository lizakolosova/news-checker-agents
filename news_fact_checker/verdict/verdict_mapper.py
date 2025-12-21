from .verdict_models import VerdictRating


def map_consensus_to_rating(evaluation: dict) -> VerdictRating:
    consensus = evaluation.get("consensus_level", "insufficient")
    confidence = evaluation.get("confidence", 0.0)

    if consensus == "strong_support" and confidence >= 0.80:
        return VerdictRating.TRUE
    if consensus in {"strong_support", "likely_true"}:
        return VerdictRating.MOSTLY_TRUE
    if consensus == "mixed":
        return VerdictRating.HALF_TRUE
    if consensus in {"likely_false"}:
        return VerdictRating.MOSTLY_FALSE
    if consensus == "strong_refutation":
        return VerdictRating.FALSE
    return VerdictRating.UNVERIFIABLE