import pytest

from news_fact_checker.evidence import EvidenceEvaluationAgent

from news_fact_checker.config import DEFAULT_EVIDENCE_CONFIG


@pytest.fixture
def agent():
    return EvidenceEvaluationAgent(config=DEFAULT_EVIDENCE_CONFIG)


@pytest.fixture
def valid_evidence():
    return {
        "claim_id": "c1",
        "source_url": "https://www.bbc.com/news/example",
        "source_title": "Economic Report 2023",
        "snippet": "The economy grew by 3 percent in 2023 according to official data.",
        "published_date": "2023-06-01",
    }

def test_empty_evidence_returns_default(agent):
    result = agent.evaluate_evidence("Test claim", [])

    assert result["retrieval_status"] == "no_evidence"
    assert result["confidence"] == 0.0
    assert result["consensus_level"] == "insufficient"


def test_single_source_evaluation(agent, valid_evidence):
    claim = "The economy grew by 3 percent in 2023."
    result = agent.evaluate_evidence(claim, [valid_evidence])

    assert result["retrieval_status"] in {"ok", "weak_fit"}
    assert len(result["evaluated_sources"]) == 1

    source = result["evaluated_sources"][0]
    assert "stance" in source
    assert "credibility_score" in source
    assert "quality_score" in source
    assert "evidence_fit" in source


def test_implicit_refutation_triggered(agent):
    claim = "The economy grew by 10 percent in 2010."
    evidence = [{
        "claim_id": "c2",
        "source_url": "https://example.com",
        "source_title": "Unrelated Article",
        "snippet": "The economy stagnated in 2022.",
        "published_date": "2022-01-01",
    }]

    result = agent.evaluate_evidence(claim, evidence)

    assert result["retrieval_status"] == "weak_fit"
    assert result["consensus_level"] == "likely_false"
    assert result["avg_evidence_fit"] < 0.35
    assert result["confidence"] <= 0.75

def test_batch_evaluate(agent, valid_evidence):
    batch = [
        {
            "claim": "The economy grew by 3 percent in 2023.",
            "evidence": [valid_evidence],
        },
        {
            "claim": "Inflation reached 20 percent in 1990.",
            "evidence": [],
        },
    ]

    results = agent.batch_evaluate(batch)

    assert len(results) == 2
    assert results[0]["claim_id"] == "c1"
    assert results[1]["retrieval_status"] == "no_evidence"