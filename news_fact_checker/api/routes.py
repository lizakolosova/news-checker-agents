import asyncio
import os
import time
import traceback

import structlog
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

from news_fact_checker.claim_extraction.agent import ClaimExtractionAgent
from news_fact_checker.evidence_evaluation.agent import EvidenceEvaluationAgent
from news_fact_checker.research.agent import ResearchAgent
from news_fact_checker.research.config import ResearchConfig
from news_fact_checker.verdict.agent import VerdictAgent
from .schemas import ArticleRequest

load_dotenv(override=True)

logger = structlog.get_logger().bind(component="api")
router = APIRouter()


def run_factcheck_pipeline(payload: ArticleRequest) -> dict:
    t0 = time.time()

    try:
        extractor = ClaimExtractionAgent()

        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            raise ValueError("SERPER_API_KEY not set in environment")

        research_config = ResearchConfig(
            search_api_key=api_key,
            min_evidence=3,
            max_evidence=10,
            enable_llm_planning=True,
        )
        researcher = ResearchAgent(research_config)

        evaluator = EvidenceEvaluationAgent()
        verdict_agent = VerdictAgent()

        logger.info("extracting_claims", article_id=payload.article_id)
        claims = extractor.extract_claims(payload.text)
        claims = claims[:payload.max_claims]
        logger.info("claims_extracted", count=len(claims))

        logger.info("researching_evidence", claim_count=len(claims))

        try:
            research_results = researcher.research(claims)
        except Exception as e:
            logger.error("research_failed_completely", error=str(e), error_type=type(e).__name__)
            research_results = [{
                "claim_id": c.claim_id,
                "original_claim": c.text,
                "evidence": [],
                "metadata": {"quality_score": 0.0}
            } for c in claims]

        logger.info("research_completed", results_count=len(research_results))

        by_claim_id = {r["claim_id"]: r for r in research_results}

        verdicts_out = []
        for c in claims:
            r = by_claim_id.get(c.claim_id, {})
            evidence = r.get("evidence", [])

            if not evidence:
                logger.warning("no_evidence_found", claim_id=c.claim_id)

            evaluation = evaluator.evaluate(c.text, evidence)

            verdict = verdict_agent.render_verdict(c.text, evaluation)

            verdicts_out.append({
                "claim_id": c.claim_id,
                "claim_text": verdict.claim_text,
                "rating": verdict.rating.value,
                "confidence": verdict.confidence,
                "explanation": verdict.explanation,
                "sources": verdict.key_sources,
                "meta": verdict.metadata,
            })

        duration_ms = int((time.time() - t0) * 1000)
        logger.info("pipeline_completed", duration_ms=duration_ms)

        return {
            "article_id": payload.article_id,
            "title": payload.title,
            "verdicts": verdicts_out,
            "duration_ms": duration_ms,
        }

    except Exception as e:
        logger.error("pipeline_failed", error=str(e), error_type=type(e).__name__)
        raise


@router.post("/fact-check/article")
async def fact_check_article(payload: ArticleRequest):
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, run_factcheck_pipeline, payload)
        return result

    except ValueError as e:
        logger.error("validation_error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error("api_error", error=str(e), error_type=type(e).__name__)
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Fact-checking failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    api_key = os.getenv("SERPER_API_KEY")

    ollama_available = False
    try:
        from ollama import Client as OllamaClient
        client = OllamaClient()
        client.list()
        ollama_available = True
    except:
        pass

    return {
        "status": "healthy",
        "serper_api_configured": bool(api_key),
        "ollama_available": ollama_available,
        "timestamp": int(time.time()),
    }


@router.get("/")
async def root():
    return {
        "service": "Multi-Agent News Fact Checker",
        "version": "1.0",
        "endpoints": {
            "fact_check": "/fact-check/article",
            "health": "/health",
        }
    }