from news_fact_checker.research.utils import authority_weight, get_claim_type_str
from news_fact_checker.claim_extraction.models import ClaimType


def test_authority_weight_government():
    url = "https://www.census.gov/data"
    assert authority_weight(url) >= 0.9


def test_authority_weight_mainstream_news():
    url = "https://www.bbc.com/news"
    assert authority_weight(url) == 0.6


def test_authority_weight_unknown():
    url = "https://randomblog.example"
    assert authority_weight(url) == 0.0


def test_get_claim_type_str_enum():
    class Dummy:
        claim_type = ClaimType.STATISTICAL

    assert get_claim_type_str(Dummy()) == "statistical"


def test_get_claim_type_str_missing():
    class Dummy:
        pass

    assert get_claim_type_str(Dummy()) == "unknown"
