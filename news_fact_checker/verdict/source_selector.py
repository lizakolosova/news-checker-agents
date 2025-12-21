from typing import List, Dict


def extract_key_sources(
    sources: List[Dict],
    max_sources: int = 3
) -> List[Dict[str, str]]:
    if not sources:
        return []

    ranked = sorted(
        sources,
        key=lambda s: s.get("final_score", s.get("credibility_score", 0)),
        reverse=True
    )

    return [
        {
            "title": s.get("source_title", "Unknown")[:100],
            "url": s.get("source_url", ""),
            "tier": s.get("credibility_tier", "Unknown"),
            "stance": s.get("stance", "unclear"),
        }
        for s in ranked[:max_sources]
    ]