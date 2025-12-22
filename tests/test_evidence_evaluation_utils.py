from news_fact_checker.research.scoring import assess_recency, evidence_fit
from datetime import datetime, timezone, timedelta

def test_assess_recency_recent_date():
    recent = (datetime.now(timezone.utc) - timedelta(days=10)).date().isoformat()
    score = assess_recency(recent)

    assert score == 1.0


def test_assess_recency_old_date():
    old = (datetime.now(timezone.utc) - timedelta(days=800)).date().isoformat()
    score = assess_recency(old)

    assert score == 0.4


def test_evidence_fit_strong_match():
    claim = "The economy grew by 3 percent in 2023."
    evidence = {
        "source_title": "2023 Economy Report",
        "snippet": "The economy grew by 3 percent in 2023.",
        "published_date": "2023-06-01",
    }

    fit = evidence_fit(claim, evidence)
    assert fit >= 0.8


def test_evidence_fit_report_date_mismatch_penalty():
    claim = "According to a report from June 2022, inflation fell."
    evidence = {
        "source_title": "Inflation Report",
        "snippet": "Inflation fell significantly.",
        "published_date": "2023-06-01",
    }

    fit = evidence_fit(claim, evidence)
    assert fit == 0.15
