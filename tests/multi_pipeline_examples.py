from __future__ import annotations

from dotenv import load_dotenv
load_dotenv(override=True)

from typing import Dict, List

from news_fact_checker.claim_extraction.agent import ClaimExtractionAgent
from news_fact_checker.research.agent import ResearchAgent
from news_fact_checker.evidence.agent import EvidenceEvaluationAgent
from news_fact_checker.verdict.agent import VerdictAgent
from news_fact_checker.verdict.explanation_generator import VerdictRating

RATING_EMOJI = {
    VerdictRating.TRUE: "✅",
    VerdictRating.MOSTLY_TRUE: "✓",
    VerdictRating.HALF_TRUE: "◐",
    VerdictRating.MOSTLY_FALSE: "✗",
    VerdictRating.FALSE: "❌",
    VerdictRating.UNVERIFIABLE: "❓"
}


def run_article(name: str, text: str, num_claims_to_check: int = 3) -> Dict:
    claim_agent = ClaimExtractionAgent()
    research_agent = ResearchAgent()
    evidence_agent = EvidenceEvaluationAgent()
    verdict_agent = VerdictAgent()

    print("\n" + "=" * 90)
    print(f"📰 ARTICLE: {name}")
    print("=" * 90)

    claims = claim_agent.extract_claims(text)
    print(f"\n📋 AGENT 1 - Extracted {len(claims)} verifiable claims:")
    for i, c in enumerate(claims[:num_claims_to_check], start=1):
        print(f"  {i}. {c.text[:85]}{'...' if len(c.text) > 85 else ''}")
        print(f"     Type: {c.claim_type.value.upper()} | Confidence: {c.confidence:.0%}")

    claims_to_check = claims[:num_claims_to_check]
    print(f"\n🔍 Fact-checking top {len(claims_to_check)} claims...")

    print("\n📚 AGENT 2 - Researching evidence...")
    research_results = research_agent.research_claims(claims_to_check)

    for i, rr in enumerate(research_results, start=1):
        meta = rr.get("metadata", {})
        domains = ", ".join(meta.get("detected_domains", []))
        quality = meta.get("quality_score", 0)
        tier1 = meta.get("tier1_sources", 0)
        print(f"  Claim {i}: {len(rr['evidence'])} sources | "
              f"Domains: {domains} | Quality: {quality:.2f} | Tier-1: {tier1}")

    print("\n⚖️  AGENT 3 - Evaluating evidence quality...")
    evaluations = []
    for rr in research_results:
        ev = evidence_agent.evaluate(
            claim=rr["original_claim"],
            evidence_list=rr["evidence"]
        )
        evaluations.append(ev)

        print(f"  Claim {len(evaluations)}: Consensus={ev['consensus_level']:<18} "
              f"Confidence={ev['confidence']:.0%} | "
              f"Quality={ev['evidence_quality']:.0%}")

    print("\n🎯 AGENT 4 - Rendering final verdicts...")
    verdicts = []
    for i, (claim, evaluation) in enumerate(zip(claims_to_check, evaluations), start=1):
        verdict = verdict_agent.render_verdict(
            claim=claim.text,
            evaluation=evaluation
        )
        verdicts.append(verdict)

        emoji = RATING_EMOJI.get(verdict.rating, "•")
        print(f"  {emoji} Claim {i}: {verdict.rating.value.upper().replace('_', ' '):<15} "
              f"(Confidence: {verdict.confidence:.0%})")

    # Summary
    print("\n" + "=" * 90)
    print(f"📋 ARTICLE SUMMARY: {name}")
    print("=" * 90)

    rating_dist = {}
    for v in verdicts:
        rating_dist[v.rating] = rating_dist.get(v.rating, 0) + 1

    print("\n📊 VERDICT DISTRIBUTION:")
    for rating in VerdictRating:
        count = rating_dist.get(rating, 0)
        if count > 0:
            emoji = RATING_EMOJI[rating]
            bar = "█" * count + "░" * (len(verdicts) - count)
            print(f"   {emoji} {rating.value.upper().replace('_', ' '):<18} {bar} {count}")

    avg_confidence = sum(v.confidence for v in verdicts) / len(verdicts) if verdicts else 0
    avg_credibility = sum(v.overall_credibility for v in verdicts) / len(verdicts) if verdicts else 0
    avg_quality = sum(v.evidence_quality for v in verdicts) / len(verdicts) if verdicts else 0

    print(f"\n📈 AVERAGE METRICS:")
    print(f"   Confidence: {avg_confidence:.0%}")
    print(f"   Credibility: {avg_credibility:.0%}")
    print(f"   Evidence Quality: {avg_quality:.0%}")

    return {
        "name": name,
        "claims": claims,
        "verdicts": verdicts,
        "metrics": {
            "avg_confidence": avg_confidence,
            "avg_credibility": avg_credibility,
            "avg_quality": avg_quality,
        }
    }


def main():

    print("\n" + "🔬" * 45)
    print("MULTI-DOMAIN NEWS FACT-CHECKER")
    print("4-Agent Pipeline: Extraction → Research → Evaluation → Verdict")
    print("Testing: Government Stats | Entertainment | Sports | Corporate")
    print("🔬" * 45)

    # ========================================================================
    # TEST ARTICLES - MULTIPLE DOMAINS
    # ========================================================================

    articles: List[tuple[str, str]] = [
        # ----------------------------------------------------------------
        # GOVERNMENT STATISTICS
        # ----------------------------------------------------------------
        (
            "🏛️ EU Macro Economy",
            """
            Euro area inflation fell from 10.6% in October 2022 to 2.9% in December 2023.
            According to Eurostat, the annual inflation rate was 2.9% in December 2023.
            The European Central Bank stated it would keep interest rates unchanged last week.
            """
        ),

        (
            "🏛️ Belgium Local Data",
            """
            According to Statbel, Belgium's unemployment rate was 5.6% in 2023.
            Belgium's GDP grew by 1.5% in 2023.
            The government announced that it would reduce VAT on electricity.
            """
        ),

        (
            "🏛️ US Labor Market",
            """
            The US unemployment rate was 3.7% in December 2023 according to the Bureau of Labor Statistics.
            Nonfarm payrolls increased by 216,000 jobs in December 2023.
            The labor force participation rate remained at 62.5%.
            """
        ),

        # ----------------------------------------------------------------
        # ENTERTAINMENT / CELEBRITY
        # ----------------------------------------------------------------
        (
            "🎵 Music Industry",
            """
            Taylor Swift's 'Midnights' album sold 1.6 million copies in its first week.
            The album debuted at number one on the Billboard 200 chart.
            It broke the record for most-streamed album in a single week on Spotify.
            """
        ),

        (
            "🎬 Box Office Records",
            """
            Barbie earned over $1.4 billion at the global box office in 2023.
            Oppenheimer grossed $952 million worldwide by the end of 2023.
            The Super Mario Bros Movie became the highest-grossing film of 2023.
            """
        ),

        # ----------------------------------------------------------------
        # SPORTS
        # ----------------------------------------------------------------
        (
            "🏀 NBA Statistics",
            """
            LeBron James became the NBA's all-time leading scorer in February 2023.
            He surpassed Kareem Abdul-Jabbar's record of 38,387 points.
            James achieved this milestone at age 38 in his 20th NBA season.
            """
        ),

        (
            "⚽ Soccer Results",
            """
            Manchester City won the UEFA Champions League final 1-0 against Inter Milan.
            This completed Manchester City's historic treble in the 2022-23 season.
            Rodri scored the winning goal in the 68th minute.
            """
        ),

        # ----------------------------------------------------------------
        # CORPORATE FINANCE
        # ----------------------------------------------------------------
        (
            "💼 Tech Earnings",
            """
            Apple reported record revenue of $117.2 billion in Q1 fiscal 2024.
            Microsoft's cloud revenue reached $33.7 billion in Q2 2024.
            Amazon's net income more than tripled to $10.6 billion in Q4 2023.
            """
        ),

        # ----------------------------------------------------------------
        # MIXED DOMAINS (Tests Plugin Selection)
        # ----------------------------------------------------------------
        (
            "🔀 Mixed: Tech & Economy",
            """
            Apple's market cap briefly crossed $3 trillion in January 2024.
            The US GDP grew at 3.3% annual rate in Q4 2023.
            Netflix added 13.1 million subscribers in Q4 2023.
            """
        ),

        (
            "🔀 Mixed: Sports & Entertainment",
            """
            Taylor Swift attended 13 Kansas City Chiefs games during the 2023 season.
            The Chiefs won the Super Bowl LVIII against the San Francisco 49ers.
            Swift's presence reportedly boosted NFL viewership by 20% among young women.
            """
        ),

        # ----------------------------------------------------------------
        # CHALLENGING CASES
        # ----------------------------------------------------------------
        (
            "⚠️ Temporal Trap",
            """
            A report from January 2023 said US unemployment was 3.5% in December.
            Another source states unemployment was 3.7% in December 2023.
            The national statistics office reported unemployment fell to 3.5% in December 2023.
            """
        ),

        (
            "⚠️ False Claims Mix",
            """
            The US added 250,000 jobs in December 2023 according to BLS.
            However, some analysts claim the real unemployment rate is closer to 7%.
            Consumer spending increased by 15% in Q4 2023.
            Inflation reached 2.1% in December 2023 according to the Federal Reserve.
            """
        ),

        (
            "⚠️ Fabricated Celebrity Claims",
            """
            Taylor Swift announced she will retire from music after her Eras Tour.
            Beyoncé's Renaissance tour earned $2.5 billion, breaking all records.
            Drake released 15 albums in 2023, more than any artist in history.
            """
        ),
    ]

    # ========================================================================
    # RUN PIPELINE
    # ========================================================================
    results = []
    for name, text in articles:
        result = run_article(name, text, num_claims_to_check=3)
        results.append(result)

    # ========================================================================
    # GLOBAL SUMMARY
    # ========================================================================
    print("\n\n" + "=" * 90)
    print("🌍 GLOBAL SUMMARY - ALL ARTICLES")
    print("=" * 90)

    # Aggregate by domain
    domain_stats = {
        "Government": [],
        "Entertainment": [],
        "Sports": [],
        "Corporate": [],
        "Mixed": [],
        "Challenging": []
    }

    for result in results:
        name = result["name"]
        if "🏛️" in name:
            domain_stats["Government"].append(result)
        elif "🎵" in name or "🎬" in name:
            domain_stats["Entertainment"].append(result)
        elif "🏀" in name or "⚽" in name:
            domain_stats["Sports"].append(result)
        elif "💼" in name:
            domain_stats["Corporate"].append(result)
        elif "🔀" in name:
            domain_stats["Mixed"].append(result)
        elif "⚠️" in name:
            domain_stats["Challenging"].append(result)

    print("\n📊 PERFORMANCE BY DOMAIN:")
    for domain, domain_results in domain_stats.items():
        if not domain_results:
            continue

        all_verdicts = [v for r in domain_results for v in r["verdicts"]]
        if not all_verdicts:
            continue

        avg_conf = sum(v.confidence for v in all_verdicts) / len(all_verdicts)
        avg_qual = sum(v.evidence_quality for v in all_verdicts) / len(all_verdicts)

        true_count = sum(1 for v in all_verdicts if v.rating in [VerdictRating.TRUE, VerdictRating.MOSTLY_TRUE])
        false_count = sum(1 for v in all_verdicts if v.rating in [VerdictRating.FALSE, VerdictRating.MOSTLY_FALSE])
        unverifiable = sum(1 for v in all_verdicts if v.rating == VerdictRating.UNVERIFIABLE)

        print(f"\n  {domain}:")
        print(f"    Articles: {len(domain_results)} | Claims: {len(all_verdicts)}")
        print(f"    Avg Confidence: {avg_conf:.0%} | Avg Quality: {avg_qual:.0%}")
        print(f"    ✅ True/Mostly True: {true_count} | ❌ False/Mostly False: {false_count} | ❓ Unverifiable: {unverifiable}")

    # Overall stats
    all_verdicts = [v for r in results for v in r["verdicts"]]
    global_rating_dist = {}
    for v in all_verdicts:
        global_rating_dist[v.rating] = global_rating_dist.get(v.rating, 0) + 1

    print(f"\n📊 OVERALL VERDICT DISTRIBUTION ({len(all_verdicts)} claims):")
    for rating in VerdictRating:
        count = global_rating_dist.get(rating, 0)
        if count > 0:
            emoji = RATING_EMOJI[rating]
            pct = count / len(all_verdicts) * 100
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            print(f"   {emoji} {rating.value.upper().replace('_', ' '):<18} {bar} {count:2d} ({pct:5.1f}%)")

    print(f"\n⚙️  SYSTEM PERFORMANCE:")
    total_claims = sum(len(r["claims"]) for r in results)
    claims_checked = len(all_verdicts)
    avg_confidence = sum(v.confidence for v in all_verdicts) / len(all_verdicts)
    avg_quality = sum(v.evidence_quality for v in all_verdicts) / len(all_verdicts)

    print(f"   Total claims extracted: {total_claims}")
    print(f"   Claims fact-checked: {claims_checked}")
    print(f"   Average confidence: {avg_confidence:.0%}")
    print(f"   Average evidence quality: {avg_quality:.0%}")
    print(f"   Articles processed: {len(results)}")

    # Confidence breakdown
    high_conf = sum(1 for v in all_verdicts if v.confidence >= 0.80)
    med_conf = sum(1 for v in all_verdicts if 0.60 <= v.confidence < 0.80)
    low_conf = sum(1 for v in all_verdicts if v.confidence < 0.60)

    print(f"\n📈 CONFIDENCE DISTRIBUTION:")
    print(f"   High confidence (≥80%): {high_conf} ({high_conf/len(all_verdicts)*100:.1f}%)")
    print(f"   Medium confidence (60-79%): {med_conf} ({med_conf/len(all_verdicts)*100:.1f}%)")
    print(f"   Low confidence (<60%): {low_conf} ({low_conf/len(all_verdicts)*100:.1f}%)")

    print("\n" + "✅" * 45)
    print("MULTI-DOMAIN PIPELINE COMPLETED SUCCESSFULLY")
    print("✅" * 45 + "\n")


if __name__ == "__main__":
    main()