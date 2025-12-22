from typing import Optional, List, Dict, Any

from news_fact_checker.claim_extraction.models import Claim, ClaimType
from news_fact_checker.research.query_builder import generate_queries


def authority_weight(url: str, authoritative_domains: Optional[List[str]] = None) -> float:
    """Calculate authority weight [0, 1] based on URL domain."""
    if not url:
        return 0.0

    url_lower = url.lower()

    if authoritative_domains:
        auth_lower = [d.lower() for d in authoritative_domains if d]
        if any(domain in url_lower for domain in auth_lower):
            return 1.0

    gov_markers = (".gov", ".gouv", ".gov.uk", ".gv.", ".stat.", "europa.eu", ".int")
    if any(marker in url_lower for marker in gov_markers):
        return 0.9

    news_markers = (
        "reuters.com", "apnews.com", "bbc.com", "nytimes.com",
        "ft.com", "bloomberg.com", "wsj.com", "theguardian.com",
    )
    if any(marker in url_lower for marker in news_markers):
        return 0.6

    return 0.0

def build_llm_prompt(claim_text: str, claim_type: str) -> str:
    """Build prompt for LLM query generation with strict JSON formatting."""
    return f"""You are a research strategist for a fact-checking system.

Analyze this claim and respond with ONLY a valid JSON object (no markdown, no backticks, no explanations).

Your tasks:
1. Identify the domain: government_statistics, entertainment, sports, corporate, mixed, or other
2. Create 3-6 high-quality search queries for official/reputable sources
3. Create 1-3 broader news-style queries
4. List 3-8 authoritative domains for this claim type

Required JSON format:
{{
  "domain": "government_statistics",
  "authority_queries": ["query 1", "query 2", "query 3"],
  "news_queries": ["news query 1", "news query 2"],
  "authoritative_domains": ["domain1.com", "domain2.org"]
}}

Claim type: {claim_type}
Claim: {claim_text}

JSON response:"""


def get_claim_type_str(claim: Claim) -> str:
    """Extract claim type as string."""
    claim_type = getattr(claim, "claim_type", None)
    if isinstance(claim_type, ClaimType):
        return claim_type.value
    return str(claim_type) if claim_type else "unknown"


def fallback_query_plan(claim: Claim) -> Dict[str, Any]:
    """Generate fallback query plan when LLM is unavailable."""
    base_queries = generate_queries(claim, max_queries=5)
    return {
        "domain": "unknown",
        "authority_queries": base_queries,
        "news_queries": base_queries[:2],
        "authoritative_domains": [],
        "strategy": "deterministic_fallback",
    }
