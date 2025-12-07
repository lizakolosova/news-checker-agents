import structlog
import requests
import uuid
from typing import List, Dict, Any, Optional

from config import ResearchConfig
from models import Claim
from utils import clean_claim_text, calculate_text_similarity
import os
from groq import Groq


class ResearchAgent:
    """Research Agent: Retrieves web evidence for claims."""

    def __init__(self, config: Optional[ResearchConfig] = None):
        self.config = config or ResearchConfig(
            search_api_key=os.getenv("SERPER_API_KEY", ""),
            groq_api_key=os.getenv("GROQ_API_KEY", "")
        )
        self.logger = structlog.get_logger().bind(component="researchagent")

        if not self.config.search_api_key:
            raise ValueError("SERPER_API_KEY environment variable required")
        if not self.config.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable required")

        self.groq_client = Groq(api_key=self.config.groq_api_key)

    def research_claims(self, claims: List[Claim]) -> List[Dict[str, Any]]:
        """Process claims -> evidence."""
        results = []
        for claim in claims:
            trace_id = str(uuid.uuid4())
            self.logger.info("research_started", trace_id=trace_id, claim_id=claim.claim_id)

            queries = self.generate_queries(claim)
            sources = self.search_web(queries, trace_id)
            evidence = self.extract_evidence(claim, sources, trace_id)

            results.append({
                "claim_id": claim.claim_id,
                "original_claim": claim.text,
                "claim_type": claim.claim_type.value,
                "confidence": claim.confidence,
                "queries_used": queries,
                "evidence": evidence
            })
        return results

    def generate_queries(self, claim: Claim) -> List[str]:
        """Generate optimized search queries from claim."""
        base_query = clean_claim_text(claim.text)
        entities = " ".join(claim.entities or [])
        dates = " ".join(claim.temporal_markers or [])
        numbers = " ".join([str(d.get('value', '')) for d in claim.numerical_data or []])

        queries = [base_query]
        if entities:
            queries.append(f'"{entities}" {base_query}')
        if dates:
            queries.append(f'{base_query} {dates}')
        if numbers:
            queries.append(f'{base_query} "{numbers}"')
        if claim.claim_type == "STATISTICAL":
            queries.append(f'{base_query} official statistics data')

        return queries[:self.config.max_results]

    def search_web(self, queries: List[str], trace_id: str) -> List[Dict[str, str]]:
        """Fetch sources using Serper API."""
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": self.config.search_api_key,
            "Content-Type": "application/json"
        }

        all_sources = []
        for query in queries:
            payload = {"q": query, "num": 3}
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()

                for result in data.get("organic", [])[:3]:
                    all_sources.append({
                        "url": result["link"],
                        "title": result["title"][:100],
                        "snippet": result["snippet"][:500]
                    })
            except Exception as e:
                self.logger.error("search_failed", trace_id=trace_id, query=query, error=str(e))

        # Deduplicate by URL
        seen_urls = set()
        unique_sources = []
        for source in all_sources:
            if source["url"] not in seen_urls:
                unique_sources.append(source)
                seen_urls.add(source["url"])

        self.logger.info("sources_retrieved", trace_id=trace_id, total=len(unique_sources))
        return unique_sources[:self.config.max_results]

    def extract_evidence(self, claim: Claim, sources: List[Dict], trace_id: str) -> List[Dict]:
        """Use LLM to classify evidence stance."""
        evidence = []

        print(f"DEBUG: Processing {len(sources)} sources (NO relevance filter)...")

        for source in sources:
            relevance = calculate_text_similarity(claim.text, source["snippet"])

            prompt = f"""
            Claim: "{claim.text}"
            Source: "{source['snippet'][:400]}"
            Stance: "supports", "refutes", or "unclear"? ONLY the word.
            """

            try:
                response = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=10
                )
                stance = response.choices[0].message.content.strip().lower()
                if stance not in ["supports", "refutes", "unclear"]:
                    stance = "unclear"
            except Exception as e:
                print(f"LLM Error: {e}")  # DEBUG
                stance = "unclear"

            evidence.append({
                "source_url": source["url"],
                "source_title": source["title"],
                "snippet": source["snippet"][:300],
                "relevance_score": round(relevance, 3),
                "stance": stance
            })

        print(f"Extracted {len(evidence)} evidence items")
        return evidence
