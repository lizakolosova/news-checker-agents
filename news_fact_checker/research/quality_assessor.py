from __future__ import annotations

from typing import List
import structlog

from news_fact_checker.research.models import EvidenceItem, QualityReport
from news_fact_checker.research.constants import (
    QUALITY_WEIGHTS,
    QUALITY_MIN_SOURCES,
    AUTHORITY_WEIGHTS,
)

logger = structlog.get_logger().bind(component="quality_assessor")


class QualityAssessor:

    @staticmethod
    def assess(
            evidence: List[EvidenceItem],
            has_llm: bool,
            trace_id: str,
    ) -> QualityReport:
        if not evidence:
            return QualityReport(
                quality_score=0.0,
                tier1_count=0,
                strategy_used="no_evidence",
            )

        count = len(evidence)
        avg_relevance = sum(e.get("relevance_score", 0.0) for e in evidence) / count
        size_score = min(count / QUALITY_MIN_SOURCES, 1.0)

        quality = (
                QUALITY_WEIGHTS["relevance"] * avg_relevance +
                QUALITY_WEIGHTS["size"] * size_score
        )
        quality = max(0.0, min(1.0, quality))

        tier1_count = sum(
            1 for e in evidence
            if e.get("authority_weight", 0.0) >= AUTHORITY_WEIGHTS["government"]
        )

        strategy = "llm_hybrid" if has_llm else "deterministic"

        logger.info(
            "retrieval_quality_assessed",
            trace_id=trace_id,
            quality_score=round(quality, 3),
            evidence_count=count,
            tier1_sources=tier1_count,
            avg_relevance=round(avg_relevance, 3),
            strategy=strategy,
        )

        return QualityReport(
            quality_score=round(quality, 3),
            tier1_count=tier1_count,
            strategy_used=strategy,
        )