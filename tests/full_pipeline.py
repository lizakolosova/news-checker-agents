"""
Complete Multi-Agent Fact-Checker Pipeline
Integrates all three agents: Extraction -> Research -> Evidence Evaluation
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'news_fact_checker'))

from news_fact_checker.claim_extraction.agent import ClaimExtractionAgent
from news_fact_checker.research.agent import ResearchAgent
from news_fact_checker.evidence.evidence_agent import EvidenceEvaluationAgent

article = """
The unemployment rate dropped to 3.5% in December 2023 according to the Bureau of Labor Statistics.
This represents a significant decrease compared to the previous year. President Biden announced that
the economy added 250,000 jobs last month, which economists attribute to strong consumer spending.
The Federal Reserve stated yesterday that it would maintain interest rates at current levels.
Inflation has decreased from 9.1% to 3.2% over the past year, marking a substantial improvement.
"""

print("═" * 80)
print("🤖 MULTI-AGENT FACT-CHECKER PIPELINE")
print("═" * 80)

# ============================================================================
# AGENT 1: CLAIM EXTRACTION
# ============================================================================
print("\n📋 AGENT 1: Extracting claims from article...")
print("─" * 80)

claim_agent = ClaimExtractionAgent()
claims = claim_agent.extract_claims(article)

print(f"✓ Found {len(claims)} verifiable claims\n")

for i, claim in enumerate(claims, 1):
    print(f"  {i}. {claim.text[:70]}...")
    print(f"     Type: {claim.claim_type.value.upper()} | Confidence: {claim.confidence:.1%}")

# ============================================================================
# AGENT 2: RESEARCH & EVIDENCE GATHERING
# ============================================================================
print("\n\n🔍 AGENT 2: Researching evidence for claims...")
print("─" * 80)

research_agent = ResearchAgent()

# Research first 2 claims (adjust as needed)
num_claims_to_check = min(2, len(claims))
evidence_results = research_agent.research_claims(claims[:num_claims_to_check])

for i, result in enumerate(evidence_results, 1):
    print(f"\n  Claim {i}: {result['original_claim'][:60]}...")
    print(f"  ✓ Retrieved {len(result['evidence'])} sources")

    # Show stance summary
    supports = sum(1 for e in result['evidence'] if e['stance'] == 'supports')
    refutes = sum(1 for e in result['evidence'] if e['stance'] == 'refutes')
    unclear = len(result['evidence']) - supports - refutes
    print(f"  └─ Stance: {supports} support | {refutes} refute | {unclear} unclear")

# ============================================================================
# AGENT 3: EVIDENCE EVALUATION
# ============================================================================
print("\n\n⚖️  AGENT 3: Evaluating evidence quality and credibility...")
print("─" * 80)

evidence_agent = EvidenceEvaluationAgent()

final_results = []
for research_result in evidence_results:
    evaluation = evidence_agent.evaluate_evidence(
        claim=research_result['original_claim'],
        evidence_list=research_result['evidence']
    )

    final_results.append({
        **research_result,
        "evaluation": evaluation
    })

    print(f"\n  Claim: {research_result['original_claim'][:60]}...")
    print(f"  ├─ Overall Credibility: {evaluation['overall_credibility']:.1%}")
    print(f"  ├─ Evidence Quality: {evaluation['evidence_quality']:.1%}")
    print(f"  ├─ Consensus: {evaluation['consensus_level'].replace('_', ' ').upper()}")
    print(f"  └─ Confidence: {evaluation['confidence']:.1%}")

# ============================================================================
# DETAILED FACT-CHECK RESULTS
# ============================================================================
print("\n\n" + "═" * 80)
print("📊 DETAILED FACT-CHECK RESULTS")
print("═" * 80)

for idx, result in enumerate(final_results, 1):
    evaluation = result['evaluation']

    print(f"\n{'─' * 80}")
    print(f"CLAIM #{idx}")
    print(f"{'─' * 80}")
    print(f"\n📝 TEXT: {result['original_claim']}")

    # Metadata
    print(f"\n📌 METADATA:")
    print(f"   Type: {result.get('claim_type', 'unknown').upper()}")
    print(f"   Extraction Confidence: {result.get('confidence', 0):.1%}")

    # Verdict
    print(f"\n⚖️  VERDICT:")
    consensus_emoji = {
        "strong_support": "✅ STRONGLY SUPPORTED",
        "likely_true": "✓ LIKELY TRUE",
        "mixed": "⚠️  MIXED EVIDENCE",
        "likely_false": "✗ LIKELY FALSE",
        "strong_refutation": "❌ STRONGLY REFUTED",
        "insufficient": "❓ INSUFFICIENT EVIDENCE"
    }
    verdict = consensus_emoji.get(evaluation['consensus_level'], "❓ UNKNOWN")
    print(f"   {verdict}")

    # Scores
    print(f"\n📊 SCORES:")
    print(f"   Overall Credibility: {evaluation['overall_credibility']:.1%}")
    print(f"   Evidence Quality: {evaluation['evidence_quality']:.1%}")
    print(f"   Verdict Confidence: {evaluation['confidence']:.1%}")

    # Evidence breakdown
    supports = sum(1 for e in evaluation['evaluated_sources'] if e['stance'] == 'supports')
    refutes = sum(1 for e in evaluation['evaluated_sources'] if e['stance'] == 'refutes')
    unclear = len(evaluation['evaluated_sources']) - supports - refutes

    print(f"\n📈 EVIDENCE BREAKDOWN:")
    print(f"   ✓ Supporting: {supports} sources")
    print(f"   ✗ Refuting: {refutes} sources")
    print(f"   ? Unclear: {unclear} sources")
    print(f"   Total: {len(evaluation['evaluated_sources'])} sources")

    # Reasoning
    print(f"\n💭 REASONING:")
    reasoning_lines = evaluation['reasoning'].split('. ')
    for line in reasoning_lines:
        if line.strip():
            print(f"   {line.strip()}.")

    # Top sources
    print(f"\n📚 TOP SOURCES:")
    top_sources = sorted(
        evaluation['evaluated_sources'],
        key=lambda x: x['final_score'],
        reverse=True
    )[:3]

    for i, source in enumerate(top_sources, 1):
        stance_emoji = {"supports": "✓", "refutes": "✗", "unclear": "?"}
        emoji = stance_emoji.get(source['stance'], "•")

        print(f"\n   {emoji} SOURCE {i}:")
        print(f"      Title: {source['source_title'][:60]}")
        print(f"      URL: {source['source_url']}")
        print(f"      Tier: {source['credibility_tier']}")
        print(f"      Scores: Cred={source['credibility_score']:.2f} | "
              f"Qual={source['quality_score']:.2f} | "
              f"Rel={source['relevance_score']:.2f}")
        print(f"      Snippet: {source['snippet'][:120]}...")

# ============================================================================
# PIPELINE SUMMARY
# ============================================================================
print("\n\n" + "═" * 80)
print("📊 PIPELINE SUMMARY")
print("═" * 80)

total_claims = len(final_results)
total_sources = sum(len(r['evaluation']['evaluated_sources']) for r in final_results)
avg_credibility = sum(
    r['evaluation']['overall_credibility'] for r in final_results) / total_claims if total_claims > 0 else 0
avg_confidence = sum(r['evaluation']['confidence'] for r in final_results) / total_claims if total_claims > 0 else 0

# Consensus breakdown
consensus_counts = {}
for r in final_results:
    consensus = r['evaluation']['consensus_level']
    consensus_counts[consensus] = consensus_counts.get(consensus, 0) + 1

print(f"\n📋 CLAIMS PROCESSED:")
print(f"   Total claims extracted: {len(claims)}")
print(f"   Claims fact-checked: {total_claims}")
print(f"   Total sources retrieved: {total_sources}")

print(f"\n📊 QUALITY METRICS:")
print(f"   Average credibility: {avg_credibility:.1%}")
print(f"   Average confidence: {avg_confidence:.1%}")

print(f"\n⚖️  VERDICT DISTRIBUTION:")
for consensus, count in sorted(consensus_counts.items()):
    print(f"   {consensus.replace('_', ' ').title()}: {count}")

print(f"\n✅ Multi-agent pipeline: COMPLETED")
print("═" * 80 + "\n")