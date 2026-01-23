from typing import Any, Dict
import json
import re
import structlog

from news_fact_checker.research.utils import fallback_query_plan

logger = structlog.get_logger().bind(component="research_parsing")

def parse_llm_response(
    content: str,
    claim: Any,
    trace_id: str,
) -> Dict[str, Any]:
    plan: Dict[str, Any] = {
        "domain": "unknown",
        "authority_queries": [],
        "news_queries": [],
        "authoritative_domains": [],
        "strategy": "llm",
    }

    raw = (content or "").strip()

    try:
        raw = re.sub(r'```(?:json)?\s*', '', raw)
        raw = re.sub(r'```\s*$', '', raw)

        start = raw.find("{")
        if start == -1:
            raise ValueError("No '{' found in LLM response")

        candidate = raw[start:]

        candidate = re.sub(r'\(\s*"([^"]+)"\s*\)', r'"\1"', candidate)

        try:
            plan_json = json.loads(candidate)
        except json.JSONDecodeError:
            open_braces = candidate.count("{")
            close_braces = candidate.count("}")
            if close_braces < open_braces:
                candidate += "}" * (open_braces - close_braces)

            plan_json = json.loads(candidate)

        for key in ("domain", "authority_queries", "news_queries", "authoritative_domains"):
            if key in plan_json:
                value = plan_json[key]

                if key.endswith("_queries") or key == "authoritative_domains":
                    if not isinstance(value, list):
                        value = [value] if value else []
                    value = [
                        str(item).strip('()"\' ')
                        for item in value
                        if item
                    ]

                plan[key] = value

        logger.info(
            "llm_query_plan_success",
            trace_id=trace_id,
            domain=plan["domain"],
            authority_count=len(plan["authority_queries"]),
            news_count=len(plan["news_queries"]),
        )

    except Exception as e:
        logger.warning(
            "llm_query_plan_parse_failed",
            trace_id=trace_id,
            raw_preview=raw[:400],
            error=str(e),
            error_type=type(e).__name__,
        )
        return fallback_query_plan(claim)

    return plan