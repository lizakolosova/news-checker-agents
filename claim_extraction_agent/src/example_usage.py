"""Example usage of the Claim Extraction Agent."""

import logging
from claim_extraction_agent.src import ClaimExtractionAgent
from claim_extraction_agent.src.config import ClaimExtractionConfig

logging.basicConfig(level=logging.INFO)


def main():
    """Demonstrate claim extraction."""

    sample_article = """
    The unemployment rate fell to 3.5% in December 2023, according to the Bureau 
    of Labor Statistics. This represents a significant decrease compared to the 
    previous year. President Smith stated that the economy added 250,000 jobs 
    last month, which economists say is due to strong consumer spending. 
    The Federal Reserve announced yesterday that it would maintain interest rates 
    at current levels. Inflation has decreased from 9.1% to 3.2% over the past year.
    """

    config = ClaimExtractionConfig(
        min_confidence=0.3,
        similarity_threshold=0.85
    )
    agent = ClaimExtractionAgent(config)

    claims = agent.extract_claims(
        sample_article,
        article_metadata={"source": "example.com", "date": "2024-01-15"}
    )

    print(f"\n{'=' * 60}")
    print(f"Extracted {len(claims)} claims:")
    print(f"{'=' * 60}\n")

    for i, claim in enumerate(claims, 1):
        print(f"Claim {i}:")
        print(f"  Text: {claim.text}")
        print(f"  Type: {claim.claim_type.value}")
        print(f"  Confidence: {claim.confidence:.2f} ({claim.confidence_level.value})")
        print(f"  Entities: {', '.join(claim.entities) if claim.entities else 'None'}")
        print(f"  Temporal: {', '.join(claim.temporal_markers) if claim.temporal_markers else 'None'}")
        if claim.numerical_data:
            print(f"  Numerical: {claim.numerical_data[0]['value']}")
        print()


if __name__ == "__main__":
    main()