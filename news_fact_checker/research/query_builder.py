from __future__ import annotations

import re
from typing import List

from news_fact_checker.claim_extraction.models import Claim, ClaimType
from news_fact_checker.utils import clean_claim_text


def generate_queries(claim: Claim, max_queries: int = 5) -> List[str]:
    base_query = clean_claim_text(claim.text)
    entities = " ".join(claim.entities or [])
    dates = " ".join(claim.temporal_markers or [])
    numbers = " ".join([str(d.get("value", "")) for d in (claim.numerical_data or [])])

    queries: List[str] = [base_query]

    if entities:
        queries.append(f'"{entities}" {base_query}')
    if dates:
        queries.append(f"{base_query} {dates}")
    if numbers:
        queries.append(f'{base_query} "{numbers}"')

    if claim.claim_type in {ClaimType.STATISTICAL, ClaimType.TEMPORAL}:
        queries.append(f"{base_query} official statistics")
        queries.append(f"{base_query} statistical office")
        queries.append(f"{base_query} central bank statement")
        queries.append(f"{base_query} government report")

    seen = set()
    out: List[str] = []
    for q in queries:
        q = re.sub(r"\s+", " ", q).strip()
        if q and q not in seen:
            out.append(q)
            seen.add(q)

    return out[:max_queries]