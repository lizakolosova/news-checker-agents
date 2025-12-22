import pytest

from news_fact_checker.claim_extraction.agent import ClaimExtractionAgent
from news_fact_checker.claim_extraction.models import ClaimType
from news_fact_checker.config import DEFAULT_CONFIG


@pytest.fixture
def agent():
    return ClaimExtractionAgent(config=DEFAULT_CONFIG)

def test_classify_attribution_over_statistical(agent):
    sentence = "The company reported revenues of $5 million in 2023."
    claim_type, confidence = agent._classify_sentence(sentence)

    assert claim_type == ClaimType.ATTRIBUTION
    assert confidence > 0.6

def test_classify_pure_statistical_sentence(agent):
     sentence = "Revenues reached $5 million in 2023."
     claim_type, confidence = agent._classify_sentence(sentence)

     assert claim_type == ClaimType.STATISTICAL
     assert confidence > 0.6


def test_classify_attribution_sentence(agent):
    sentence = 'The minister said, "Inflation is under control."'
    claim_type, confidence = agent._classify_sentence(sentence)

    assert claim_type == ClaimType.ATTRIBUTION
    assert confidence > 0.6


def test_classify_opinion_lowers_confidence(agent):
    sentence = "The economy might improve next year."
    claim_type, confidence = agent._classify_sentence(sentence)

    assert claim_type == ClaimType.FACTUAL
    assert confidence < 0.5

def test_verifiability_with_number_and_date(agent):
    sentence = "In 2022, unemployment fell to 4 percent."
    score, reason = agent._assess_verifiability(sentence)

    assert score >= 0.6
    assert reason == "ok"

def test_verifiability_intensifier_without_metric(agent):
    sentence = "There was a massive increase in crime."
    score, reason = agent._assess_verifiability(sentence)

    assert score < 0.3
    assert reason == "intensifier_without_metric_or_attribution"

def test_extract_single_high_confidence_claim(agent):
    sentence = "The population grew by 2 percent in 2021."
    claims = agent._extract_from_sentence(
        sentence=sentence,
        all_sentences=[sentence],
        sentence_idx=0,
        metadata=None,
    )

    assert len(claims) == 1
    claim = claims[0]

    assert claim.text.lower().startswith("the population grew")
    assert claim.claim_type == ClaimType.STATISTICAL
    assert claim.confidence >= agent.config.min_confidence
    assert "verifiability_score" in claim.metadata


def test_unverifiable_sentence_returns_no_claims(agent):
    sentence = "This seems problematic."
    claims = agent._extract_from_sentence(
        sentence=sentence,
        all_sentences=[sentence],
        sentence_idx=0,
        metadata=None,
    )

    assert claims == []

def test_sub_claim_extraction(agent):
    sentence = "The report says inflation fell, and unemployment dropped to 4 percent."
    claims = agent._extract_from_sentence(
        sentence=sentence,
        all_sentences=[sentence],
        sentence_idx=0,
        metadata=None,
    )

    assert len(claims) >= 2

    parent = claims[0]
    sub_claims = [c for c in claims if c.metadata.get("is_sub_claim")]

    assert sub_claims
    for sub in sub_claims:
        assert sub.confidence < parent.confidence
        assert sub.source_sentence == sentence

def test_deduplicate_similar_claims(agent):
    text = "GDP increased by 3 percent in 2022."
    claims = agent.extract_claims(text + " " + text)

    assert len(claims) == 1

def test_extract_claims_from_article(agent):
    article = (
        "In 2023, the economy grew by 3 percent. "
        "Experts say this growth was driven by exports. "
        "This is remarkable."
    )

    claims = agent.extract_claims(article)

    assert len(claims) >= 1
    assert all(c.confidence >= agent.config.min_confidence for c in claims)

    claim_types = {c.claim_type for c in claims}
    assert ClaimType.STATISTICAL in claim_types or ClaimType.ATTRIBUTION in claim_types
