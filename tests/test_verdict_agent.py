from unittest.mock import patch

from news_fact_checker.verdict.agent import VerdictAgent
from news_fact_checker.verdict.verdict_models import VerdictResult


def test_render_verdict_basic_case():
    agent = VerdictAgent()

    claim = "The economy grew by 3 percent in 2023."

    evaluation = {
        "claim_id": "c1",
        "confidence": 0.82,
        "consensus_level": "likely_true",
        "retrieval_status": "ok",
        "evidence_quality": 0.7,
        "overall_credibility": 0.75,
        "evaluated_sources": [
            {"stance": "supports", "source": "A"},
            {"stance": "supports", "source": "B"},
            {"stance": "refutes", "source": "C"},
        ],
    }

    with patch(
        "news_fact_checker.verdict.agent.map_consensus_to_rating",
        return_value="True",
    ), patch(
        "news_fact_checker.verdict.agent.generate_explanation",
        return_value="Explanation text",
    ), patch(
        "news_fact_checker.verdict.agent.extract_key_sources",
        return_value=["A", "B"],
    ):
        result = agent.render_verdict(claim, evaluation)

    assert isinstance(result, VerdictResult)

    assert result.claim_id == "c1"
    assert result.claim_text == claim
    assert result.rating == "True"
    assert result.confidence == 0.82

    assert result.supporting_evidence_count == 2
    assert result.refuting_evidence_count == 1

    assert result.evidence_quality == 0.7
    assert result.overall_credibility == 0.75

    assert result.key_sources == ["A", "B"]
    assert result.explanation == "Explanation text"

    assert result.metadata == {
        "consensus_level": "likely_true",
        "retrieval_status": "ok",
    }
def test_render_verdict_no_sources():
    agent = VerdictAgent()

    evaluation = {
        "claim_id": "c2",
        "confidence": 0.0,
        "evaluated_sources": [],
    }

    with patch(
        "news_fact_checker.verdict.agent.map_consensus_to_rating",
        return_value="Insufficient",
    ), patch(
        "news_fact_checker.verdict.agent.generate_explanation",
        return_value="No evidence available",
    ), patch(
        "news_fact_checker.verdict.agent.extract_key_sources",
        return_value=[],
    ):
        result = agent.render_verdict("Test claim", evaluation)

    assert result.supporting_evidence_count == 0
    assert result.refuting_evidence_count == 0
    assert result.rating == "Insufficient"
