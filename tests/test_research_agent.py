import pytest
from unittest.mock import MagicMock

from news_fact_checker.research.agent import ResearchAgent
from news_fact_checker.research.parsing import parse_llm_response
from news_fact_checker import Claim
from news_fact_checker.config import ResearchConfig


@pytest.fixture
def agent():
    config = ResearchConfig(
        search_api_key="test",
        groq_api_key=""
    )
    agent = ResearchAgent(config=config, llm_client=None)
    agent.serper = MagicMock()
    return agent

@pytest.fixture
def claim():
    return Claim(
        claim_id="c1",
        text="The economy grew by 3 percent in 2023.",
        claim_type=None,
    )

def test_research_claims_empty(agent):
    assert agent.research_claims([]) == []


def test_generate_query_plan_fallback(agent, claim):
    plan = agent._generate_query_plan(claim, trace_id="t1")

    assert "authority_queries" in plan
    assert "news_queries" in plan
    assert plan["strategy"] in {"heuristic", "fallback"}


def test_research_claims_happy_path(agent, claim):
    agent._generate_query_plan = MagicMock(return_value={
        "authority_queries": ["GDP 2023"],
        "news_queries": [],
        "authoritative_domains": [],
        "strategy": "test",
    })

    agent._progressive_retrieval = MagicMock(return_value=[
        {"relevance_score": 0.8, "authority_weight": 1.0}
    ])

    agent._assess_quality = MagicMock(return_value={
        "quality_score": 0.75,
        "tier1_count": 1,
    })

    results = agent.research_claims([claim])

    assert len(results) == 1
    assert results[0]["claim_id"] == "c1"
    assert results[0]["metadata"]["quality_score"] == 0.75

def test_parse_llm_response_valid_json(claim):
    content = """
    ```json
    {
      "domain": "economy",
      "authority_queries": ["GDP growth 2023"],
      "news_queries": ["economy grew 3 percent"],
      "authoritative_domains": ["bbc.com"]
    }
    ```
    """

    plan = parse_llm_response(content, claim, "t1")

    assert plan["domain"] == "economy"
    assert "GDP growth 2023" in plan["authority_queries"]

def test_parse_llm_response_malformed(claim):
    plan = parse_llm_response("nonsense text", claim, "t1")

    assert "authority_queries" in plan
    assert plan["strategy"] != "llm"
