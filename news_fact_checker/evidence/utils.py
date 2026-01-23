from __future__ import annotations

import re
from typing import Set, List, Dict, Any
from urllib.parse import urlparse

from news_fact_checker.evidence.constants import (
    NUMBER_COMPATIBILITY_THRESHOLD,
    MIN_KEY_TERM_LENGTH,
    MONTHS,
)

from news_fact_checker.evidence.constants import ATTRIBUTION_PATTERNS


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def extract_domain(url: str) -> str:
    if not url:
        return ""
    try:
        domain = urlparse(url).netloc.lower()
        return domain.replace("www.", "")
    except Exception:
        return ""


def extract_years(text: str) -> Set[str]:
    return set(re.findall(r"\b(19\d{2}|20\d{2})\b", text or ""))


def extract_months(text: str) -> Set[str]:
    tokens = set(re.findall(r"[a-z]+", (text or "").lower()))
    return tokens.intersection(set(MONTHS))


def extract_numbers(text: str) -> Set[str]:
    return set(re.findall(r"\b\d+(?:\.\d+)?%?\b", text))


def extract_key_terms(text: str, min_length: int = MIN_KEY_TERM_LENGTH) -> Set[str]:
    words = re.findall(r"[a-z]{" + str(min_length) + r",}", text.lower())
    return set(words)


def to_float(number_str: str) -> float:
    return float(number_str.rstrip("%"))


def numbers_compatible(claim: str, evidence: str) -> bool:
    claim_nums = extract_numbers(claim)
    if not claim_nums:
        return True

    ev_nums = extract_numbers(evidence)
    if not ev_nums:
        return False

    for cn in claim_nums:
        c_val = to_float(cn)
        for en in ev_nums:
            e_val = to_float(en)
            if e_val == 0:
                continue
            rel_diff = abs(c_val - e_val) / max(abs(e_val), 1.0)
            if rel_diff <= NUMBER_COMPATIBILITY_THRESHOLD:
                return True

    return False


def calculate_term_overlap(claim: str, evidence: str) -> tuple[int, float]:
    claim_terms = extract_key_terms(claim)
    evidence_terms = extract_key_terms(evidence)
    common_terms = claim_terms & evidence_terms

    overlap_count = len(common_terms)
    overlap_ratio = overlap_count / len(claim_terms) if claim_terms else 0.0

    return overlap_count, overlap_ratio


def looks_like_attribution_claim(claim: str) -> bool:
    c = (claim or "").lower()
    return any(pattern in c for pattern in ATTRIBUTION_PATTERNS)


def extract_attribution_entities(claim: str) -> List[str]:
    c = (claim or "").strip()
    m = re.search(r"(?i)\baccording to\s+([^.,;:]+)", c)
    if not m:
        return []

    entity = m.group(1).strip()
    entity = re.sub(r"(?i)^(the|a|an)\s+", "", entity).strip()
    words = entity.split()
    entity = " ".join(words[:8]).strip()

    return [entity] if entity else []


def normalize_confidence(confidence: Any) -> int:
    try:
        value = float(confidence)
        if 0.0 <= value <= 100.0:
            return int(round(value))
        if 0.0 <= value <= 1.0:
            return int(round(value * 100))
    except (TypeError, ValueError):
        pass
    return 50


def calculate_average(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def count_by_key(items: List[Dict], key: str, valid_values: Set[str]) -> Dict[str, int]:
    counts = {value: 0 for value in valid_values}
    for item in items:
        value = item.get(key)
        if value in counts:
            counts[value] += 1
    return counts