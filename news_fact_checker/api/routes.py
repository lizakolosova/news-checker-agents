import asyncio
import time

import structlog
from fastapi import APIRouter

from news_fact_checker.claim_extraction.agent import ClaimExtractionAgent
from news_fact_checker.evidence.evidence_agent import EvidenceEvaluationAgent
from news_fact_checker.research.agent import ResearchAgent
from news_fact_checker.verdict.verdict_agent import VerdictAgent
from .schemas import ArticleRequest

logger = structlog.get_logger().bind(component="api")
router = APIRouter()

def run_factcheck_pipeline(payload: ArticleRequest) -> dict:
    t0 = time.time()

    extractor = ClaimExtractionAgent()
    researcher = ResearchAgent()
    evaluator = EvidenceEvaluationAgent()
    verdict_agent = VerdictAgent()


    claims = extractor.extract_claims(payload.text)
    claims = claims[: payload.max_claims]

    research_results = researcher.research_claims(claims)
    print("research_results:", research_results)

    by_claim_id = {r["claim_id"]: r for r in (research_results or [])}

    verdicts_out = []
    for c in claims:
        r = by_claim_id.get(c.claim_id, {})
        evidence = r.get("evidence", []) or r.get("sources", []) or []

        evaluation = evaluator.evaluate_evidence(c.text, evidence)
        verdict = verdict_agent.render_verdict(c.text, evaluation)

        verdicts_out.append({
            "claim_id": getattr(c, "claim_id", None),
            "claim_text": verdict.claim_text,
            "rating": verdict.rating.value,
            "confidence": verdict.confidence,
            "explanation": verdict.explanation,
            "sources": verdict.key_sources,
            "meta": verdict.metadata,
        })

    return {
        "article_id": payload.article_id,
        "title": payload.title,
        "verdicts": verdicts_out,
        "duration_ms": int((time.time() - t0) * 1000),
    }

import traceback

@router.post("/fact-check/article")
async def fact_check_article(payload: ArticleRequest):
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, run_factcheck_pipeline, payload)
    except Exception:
        traceback.print_exc()
        raise