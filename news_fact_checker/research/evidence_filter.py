from __future__ import annotations

from typing import List, Dict, Any, Tuple
from news_fact_checker.utils import calculate_text_similarity
from news_fact_checker.claim_extraction.models import Claim


def filter_low_signal(sources: List[Dict[str, str]], low_signal_domains: Tuple[str, ...]) -> List[Dict[str, str]]:
    out = []
    for s in sources:
        url = s.get("url", "") or ""
        if url and not any(dom in url for dom in low_signal_domains):
            out.append(s)
    return out


def score_and_keep(
    claim: Claim,
    sources: List[Dict[str, str]],
    min_relevance: float,
    keep_top_k_if_all_filtered: int,
) -> List[Dict[str, Any]]:
    scored: List[Dict[str, Any]] = []
    for src in sources:
        snippet = (src.get("snippet") or "").strip()
        title = (src.get("title") or "").strip()
        text = snippet or title
        if not text:
            continue

        rel = calculate_text_similarity(claim.text, text)
        scored.append(
            {
                "source_url": src.get("url", ""),
                "source_title": src.get("title", ""),
                "snippet": (snippet or title)[:300],
                "relevance_score": round(rel, 3),
                "_raw_relevance": rel,
            }
        )

    kept = [s for s in scored if s["_raw_relevance"] >= min_relevance]
    if not kept and scored:
        kept = sorted(scored, key=lambda x: x["_raw_relevance"], reverse=True)[:keep_top_k_if_all_filtered]
    return kept
