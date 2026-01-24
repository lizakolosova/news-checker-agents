import sys
import os
from dotenv import load_dotenv

load_dotenv(override=True)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from news_fact_checker.claim_extraction.agent import ClaimExtractionAgent
from news_fact_checker.research.agent import ResearchAgent
from news_fact_checker.research.config import ResearchConfig
from news_fact_checker.evidence.agent import EvidenceEvaluationAgent

article = """
The unemployment rate dropped to 3.5% in December 2023 according to the Bureau of Labor Statistics.
This represents a significant decrease compared to the previous year. President Biden announced that
the economy added 250,000 jobs last month, which economists attribute to strong consumer spending.
The Federal Reserve stated yesterday that it would maintain interest rates at current levels.
Inflation has decreased from 9.1% to 3.2% over the past year, marking a substantial improvement.
"""

print("=" * 80)
print("🤖 MULTI-AGENT FACT-CHECKER (with Ollama)")
print("=" * 80)

try:
    from ollama import Client as OllamaClient

    print("\n✓ Ollama package found")

    try:
        client = OllamaClient()
        client.list()
        print("✓ Ollama is running")
        ollama_available = True
    except Exception as e:
        print(f"✗ Ollama not running: {e}")
        print("  Start Ollama: Run 'ollama serve' in another terminal")
        ollama_available = False
except ImportError:
    print("\n✗ Ollama not installed")
    print("  Install: pip install ollama")
    ollama_available = False

print("\n📋 AGENT 1: Extracting claims...")
print("-" * 80)

claim_agent = ClaimExtractionAgent()
claims = claim_agent.extract_claims(article)

print(f"✓ Found {len(claims)} verifiable claims\n")

for i, claim in enumerate(claims, 1):
    print(f"  {i}. {claim.text[:70]}...")
    print(f"     Type: {claim.claim_type.value.upper()} | Confidence: {claim.confidence:.1%}")

print("\n\n🔍 AGENT 2: Researching evidence...")
print("-" * 80)

api_key = os.getenv("SERPER_API_KEY")
if not api_key:
    print("❌ SERPER_API_KEY not set!")
    exit(1)

print(f"✓ Using API key: {api_key[:10]}...{api_key[-4:]}")

research_config = ResearchConfig(
    search_api_key=api_key,
    min_evidence=3,
    max_evidence=10,
    enable_llm_planning=ollama_available,
)

if ollama_available:
    print("✓ Using Ollama for query planning")
else:
    print("✓ Using heuristic query planning (Ollama not available)")

research_agent = ResearchAgent(research_config)

num_claims_to_check = min(2, len(claims))
research_results = research_agent.research(claims[:num_claims_to_check])

for i, result in enumerate(research_results, 1):
    print(f"\n  Claim {i}: {result['original_claim'][:60]}...")
    print(f"  ✓ Retrieved {len(result['evidence'])} sources")
    print(f"  └─ Quality: {result['metadata']['quality_score']:.1%}")

print("\n\n⚖️  AGENT 3: Evaluating evidence...")
print("-" * 80)

evidence_agent = EvidenceEvaluationAgent()

final_results = []
for research_result in research_results:
    evaluation = evidence_agent.evaluate(
        claim=research_result['original_claim'],
        evidence_list=research_result['evidence']
    )

    final_results.append({
        **research_result,
        "evaluation": evaluation
    })

    print(f"\n  Claim: {research_result['original_claim'][:60]}...")
    print(f"  ├─ Credibility: {evaluation['overall_credibility']:.1%}")
    print(f"  ├─ Quality: {evaluation['evidence_quality']:.1%}")
    print(f"  ├─ Consensus: {evaluation['consensus_level'].replace('_', ' ').upper()}")
    print(f"  └─ Confidence: {evaluation['confidence']:.1%}")

print("\n\n" + "=" * 80)
print("📊 DETAILED RESULTS")
print("=" * 80)

for idx, result in enumerate(final_results, 1):
    evaluation = result['evaluation']

    print(f"\n{'-' * 80}")
    print(f"CLAIM #{idx}")
    print(f"{'-' * 80}")
    print(f"\n📝 {result['original_claim']}")

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

    print(f"\n📊 SCORES:")
    print(f"   Credibility: {evaluation['overall_credibility']:.1%}")
    print(f"   Quality: {evaluation['evidence_quality']:.1%}")
    print(f"   Confidence: {evaluation['confidence']:.1%}")

    supports = sum(1 for e in evaluation['evaluated_sources'] if e.get('stance') == 'supports')
    refutes = sum(1 for e in evaluation['evaluated_sources'] if e.get('stance') == 'refutes')
    unclear = len(evaluation['evaluated_sources']) - supports - refutes

    print(f"\n📈 EVIDENCE:")
    print(f"   ✓ Supporting: {supports}")
    print(f"   ✗ Refuting: {refutes}")
    print(f"   ? Unclear: {unclear}")
    print(f"   Total: {len(evaluation['evaluated_sources'])}")

    print(f"\n💭 REASONING:")
    for line in evaluation['reasoning'].split('. '):
        if line.strip():
            print(f"   {line.strip()}.")

    print(f"\n📚 TOP SOURCES:")
    top_sources = sorted(
        evaluation['evaluated_sources'],
        key=lambda x: x.get('final_score', 0),
        reverse=True
    )[:3]

    for i, source in enumerate(top_sources, 1):
        stance_emoji = {"supports": "✓", "refutes": "✗", "unclear": "?"}
        emoji = stance_emoji.get(source.get('stance', 'unclear'), "•")

        print(f"\n   {emoji} SOURCE {i}:")
        print(f"      {source.get('source_title', 'N/A')[:60]}")
        print(f"      {source.get('source_url', 'N/A')}")
        print(f"      Tier {source.get('credibility_tier', 0)} | "
              f"Cred={source.get('credibility_score', 0):.2f} | "
              f"Qual={source.get('quality_score', 0):.2f}")

print("\n\n" + "=" * 80)
print("📊 SUMMARY")
print("=" * 80)

total = len(final_results)
total_sources = sum(len(r['evaluation']['evaluated_sources']) for r in final_results)
avg_cred = sum(r['evaluation']['overall_credibility'] for r in final_results) / total if total > 0 else 0
avg_conf = sum(r['evaluation']['confidence'] for r in final_results) / total if total > 0 else 0

consensus_counts = {}
for r in final_results:
    consensus = r['evaluation']['consensus_level']
    consensus_counts[consensus] = consensus_counts.get(consensus, 0) + 1

print(f"\n📋 CLAIMS:")
print(f"   Extracted: {len(claims)}")
print(f"   Fact-checked: {total}")
print(f"   Sources: {total_sources}")

print(f"\n📊 QUALITY:")
print(f"   Avg credibility: {avg_cred:.1%}")
print(f"   Avg confidence: {avg_conf:.1%}")

print(f"\n⚖️  VERDICTS:")
for consensus, count in sorted(consensus_counts.items()):
    print(f"   {consensus.replace('_', ' ').title()}: {count}")

if ollama_available:
    print(f"\n🤖 LLM: Ollama (llama3)")
else:
    print(f"\n🤖 LLM: Heuristics (Ollama unavailable)")

print(f"\n✅ Pipeline completed")
print("=" * 80 + "\n")