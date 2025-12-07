import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
load_dotenv()

from extractor_agent import ClaimExtractionAgent
from research_agent import ResearchAgent

article = """
Unemployment rate dropped to 3.5% in December 2023 according to Bureau of Labor Statistics.
President Trump announced 250,000 jobs added last month.
Inflation fell from 9.1% to 3.2% over past year.
Federal Reserve will maintain current interest rates.
"""

print(" MULTI-AGENT FACT-CHECKER ")
print("=" * 50)

# Agent 1
print("\n AGENT 1: Extracting claims...")
claim_agent = ClaimExtractionAgent()
claims = claim_agent.extract_claims(article)
print(f" Found {len(claims)} claims")

for i, claim in enumerate(claims, 1):
    print(f"  {i}. {claim.text[:60]}... [{claim.claim_type.value}]")

# Agent 2
print("\n AGENT 2: Researching evidence...")
research_agent = ResearchAgent()
evidence_results = research_agent.research_claims(claims[:2])

print("\n FACT-CHECK RESULTS")
print("=" * 80)
for result in evidence_results:
    print(f"\n CLAIM: {result['original_claim']}")
    print(f"   Type: {result.get('claim_type', 'unknown').upper()} | Confidence: {result.get('confidence', 0):.1%}")

    supports = sum(1 for ev in result['evidence'] if ev['stance'] == 'supports')
    refutes = sum(1 for ev in result['evidence'] if ev['stance'] == 'refutes')
    unclear = len(result['evidence']) - supports - refutes

    print(f"   Evidence Summary: {supports} supports {refutes} disprove  {unclear} unclear (Total: {len(result['evidence'])} sources)")

    print("   SOURCES:")
    for ev in result['evidence']:
        stance_emoji = {"supports": " SUPPORTS", "disprove": " DISPROVE", "unclear": " UNCLEAR"}
        emoji = stance_emoji.get(ev['stance'], " UNKNOWN")
        print(f"     • {emoji} {ev['source_title'][:70]}...")
        print(f"       Rel: {ev['relevance_score']:.1%} | {ev['snippet'][:120]}...")
        print(f"       URL: {ev['source_url']}")
        print()
    print("-" * 80)

print("\n PIPELINE SUMMARY")
total_claims = len(evidence_results)
total_evidence = sum(len(r['evidence']) for r in evidence_results)
print(f" Processed {total_claims} claims")
print(f" Retrieved {total_evidence} web sources")
print(f" Multi-agent pipeline: COMPLETED ")

