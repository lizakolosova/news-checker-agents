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