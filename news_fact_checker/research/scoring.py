from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
import re


def assess_recency(published_date: Optional[str] = None) -> float:
    if not published_date:
        return 0.7
    try:
        ds = published_date.strip()
        if len(ds) == 10:
            dt = datetime.fromisoformat(ds).replace(tzinfo=timezone.utc)
        else:
            ds = ds.replace("Z", "+00:00")
            dt = datetime.fromisoformat(ds)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        age_days = max(0.0, (now - dt).total_seconds() / 86400.0)

        if age_days <= 30: return 1.0
        if age_days <= 365: return max(0.6, 1.0 - (age_days - 30) / 600.0)
        return 0.4
    except Exception:
        return 0.7


def evidence_fit(claim: str, evidence: Dict[str, Any]) -> float:
    text = f"{evidence.get('source_title', '')} {evidence.get('snippet', '')}".lower()
    c = (claim or "").lower()

    claim_report_dates = re.findall(r"report from (\w+ \d{4})", c)
    if claim_report_dates:
        pub_date = evidence.get("published_date", "")
        for report_date in claim_report_dates:
            if report_date.lower() not in text and report_date.lower() not in pub_date.lower():
                return 0.15

    claim_nums = re.findall(r"\b\d+(?:\.\d+)?\b", c)
    ev_nums = set(re.findall(r"\b\d+(?:\.\d+)?\b", text))
    num_match = 1.0
    if claim_nums:
        hits = sum(1 for n in claim_nums if n in ev_nums)
        num_match = hits / len(claim_nums)

    claim_years = set(re.findall(r"\b(19\d{2}|20\d{2})\b", c))
    ev_years = set(re.findall(r"\b(19\d{2}|20\d{2})\b", text))
    year_match = 1.0
    if claim_years:
        year_match = 1.0 if (claim_years & ev_years) else 0.4

    claim_keywords = set([w for w in re.findall(r"[a-z]{3,}", c)])
    ev_keywords = set(re.findall(r"[a-z]{3,}", text))
    kw_overlap = len(claim_keywords & ev_keywords) / len(claim_keywords) if claim_keywords else 0.0

    fit = (0.50 * num_match) + (0.25 * year_match) + (0.25 * kw_overlap)
    return float(max(0.0, min(1.0, fit)))


def calculate_overall_credibility(sources: List[Dict]) -> float:
    if not sources:
        return 0.0

    total_weight = sum(
        s.get('relevance_score', 1.0) *
        s.get('evidence_fit', 1.0) *
        s.get('recency_score', 1.0)
        for s in sources
    )

    if total_weight == 0:
        return sum(s['credibility_score'] for s in sources) / len(sources)

    weighted_sum = sum(
        s['credibility_score'] *
        s.get('relevance_score', 1.0) *
        s.get('evidence_fit', 1.0) *
        s.get('recency_score', 1.0)
        for s in sources
    )
    return weighted_sum / total_weight


def calculate_average_quality(sources: List[Dict]) -> float:
    if not sources:
        return 0.0
    return sum(s['quality_score'] for s in sources) / len(sources)


def calculate_confidence(sources: List[Dict], consensus: str) -> float:
    if not sources:
        return 0.0

    if len(sources) < 2:
        return 0.35

    source_factor = min(len(sources) / 5.0, 1.0)

    consensus_scores = {
        "strong_support": 0.90,
        "strong_refutation": 0.90,
        "likely_true": 0.70,
        "likely_false": 0.70,
        "mixed": 0.40,
        "insufficient": 0.25,
    }
    consensus_factor = consensus_scores.get(consensus, 0.30)

    avg_cred = sum(s.get("credibility_score", 0.5) for s in sources) / len(sources)
    avg_fit = sum(s.get("evidence_fit", 1.0) for s in sources) / len(sources)
    max_fit = max(s.get("evidence_fit", 1.0) for s in sources)
    avg_quality = sum(s.get("quality_score", 0.5) for s in sources) / len(sources)

    base = (
        0.25 * source_factor +
        0.40 * consensus_factor +
        0.15 * avg_cred +
        0.10 * avg_fit +
        0.10 * avg_quality
    )

    if max_fit < 0.30:
        base = min(base, 0.40)
    elif max_fit < 0.50:
        base = min(base, 0.65)
    elif max_fit < 0.70:
        base = min(base, 0.80)

    return float(max(0.0, min(1.0, base)))


def empty_evaluation() -> Dict[str, Any]:
    return {
        "claim_id": "unknown",
        "retrieval_status": "no_evidence",
        "avg_evidence_fit": 0.0,
        "overall_credibility": 0.0,
        "evidence_quality": 0.0,
        "consensus_level": "insufficient",
        "evaluated_sources": [],
        "confidence": 0.0,
        "reasoning": "No evidence_evaluation sources available for evaluation."
    }

