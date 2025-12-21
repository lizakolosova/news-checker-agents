import structlog
from .verdict_models import VerdictResult
from .verdict_mapper import map_consensus_to_rating
from .source_selector import extract_key_sources
from .explanation_generator import generate_explanation


class VerdictAgent:
    def __init__(self):
        self.logger = structlog.get_logger().bind(component="verdict_agent")

    @staticmethod
    def render_verdict(claim: str, evaluation: dict) -> VerdictResult:
        rating = map_consensus_to_rating(evaluation)

        sources = evaluation.get("evaluated_sources", [])
        supporting = sum(1 for s in sources if s.get("stance") == "supports")
        refuting = sum(1 for s in sources if s.get("stance") == "refutes")

        result = VerdictResult(
            claim_id=evaluation.get("claim_id", "unknown"),
            claim_text=claim,
            rating=rating,
            confidence=evaluation.get("confidence", 0.0),
            explanation=generate_explanation(
                claim, rating, evaluation, supporting, refuting
            ),
            supporting_evidence_count=supporting,
            refuting_evidence_count=refuting,
            evidence_quality=evaluation.get("evidence_quality", 0.0),
            overall_credibility=evaluation.get("overall_credibility", 0.0),
            key_sources=extract_key_sources(sources),
            metadata={
                "consensus_level": evaluation.get("consensus_level"),
                "retrieval_status": evaluation.get("retrieval_status"),
            },
        )

        return result