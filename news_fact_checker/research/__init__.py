from news_fact_checker.research.agent import ResearchAgent
from news_fact_checker.research.config import ResearchConfig
from news_fact_checker.research.models import (
    QueryPlan,
    EvidenceItem,
    ResearchResult,
    QualityReport,
    SearchMetrics,
    ResearchMetrics,
)

__version__ = "2.0.0"

__all__ = [
    "ResearchAgent",
    "ResearchConfig",
    "QueryPlan",
    "EvidenceItem",
    "ResearchResult",
    "QualityReport",
    "SearchMetrics",
    "ResearchMetrics",
]