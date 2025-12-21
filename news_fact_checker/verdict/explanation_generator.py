from .verdict_models import VerdictRating


def generate_explanation(
    claim: str,
    rating: VerdictRating,
    evaluation: dict,
    supporting: int,
    refuting: int
) -> str:
    confidence = evaluation.get("confidence", 0.0)
    fit = evaluation.get("avg_evidence_fit", 0.0)
    total = len(evaluation.get("evaluated_sources", []))

    templates = {
        VerdictRating.TRUE:
            f"This claim is TRUE. {supporting} of {total} sources confirm it "
            f"with {confidence:.0%} confidence.",

        VerdictRating.MOSTLY_TRUE:
            f"This claim is MOSTLY TRUE. Evidence supports it, "
            f"though some details may vary.",

        VerdictRating.HALF_TRUE:
            f"This claim is PARTIALLY TRUE. Evidence is mixed.",

        VerdictRating.MOSTLY_FALSE:
            f"This claim is MOSTLY FALSE. Evidence contradicts key elements.",

        VerdictRating.FALSE:
            f"This claim is FALSE. Reliable sources clearly refute it.",

        VerdictRating.UNVERIFIABLE:
            f"This claim is UNVERIFIABLE due to insufficient reliable evidence.",
    }

    return templates.get(rating, "Unable to determine verdict.")