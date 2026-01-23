from __future__ import annotations

import json
import re
import structlog

from news_fact_checker.claim_extraction.models import Claim
from news_fact_checker.research.models import QueryPlan

logger = structlog.get_logger().bind(component="plan_parser")


class QueryPlanParser:

    def parse(self, content: str, claim: Claim, trace_id: str) -> QueryPlan:
        try:
            cleaned = self._clean_content(content)
            data = self._extract_json(cleaned)
            plan = self._build_plan(data)

            logger.info(
                "llm_query_plan_success",
                trace_id=trace_id,
                domain=plan["domain"],
                authority_count=len(plan["authority_queries"]),
                news_count=len(plan["news_queries"]),
            )

            return plan

        except Exception as e:
            logger.warning(
                "llm_query_plan_parse_failed",
                trace_id=trace_id,
                raw_preview=content[:400] if content else "",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def _clean_content(self, content: str) -> str:
        if not content:
            raise ValueError("Empty content")

        raw = content.strip()

        raw = re.sub(r'```(?:json)?\s*', '', raw)
        raw = re.sub(r'```\s*$', '', raw)

        return raw

    def _extract_json(self, content: str) -> dict:
        start = content.find("{")
        if start == -1:
            raise ValueError("No '{' found in LLM response")

        candidate = content[start:]

        candidate = re.sub(r'\(\s*"([^"]+)"\s*\)', r'"\1"', candidate)

        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            candidate = self._fix_braces(candidate)
            return json.loads(candidate)

    def _fix_braces(self, content: str) -> str:
        open_braces = content.count("{")
        close_braces = content.count("}")

        if close_braces < open_braces:
            content += "}" * (open_braces - close_braces)

        return content

    def _build_plan(self, data: dict) -> QueryPlan:
        plan: QueryPlan = {
            "domain": "unknown",
            "authority_queries": [],
            "news_queries": [],
            "authoritative_domains": [],
            "strategy": "llm",
        }

        for key in ("domain", "authority_queries", "news_queries", "authoritative_domains"):
            if key not in data:
                continue

            value = data[key]

            if key.endswith("_queries") or key == "authoritative_domains":
                if not isinstance(value, list):
                    value = [value] if value else []

                value = [
                    str(item).strip('()"\' ')
                    for item in value
                    if item
                ]

            plan[key] = value

        return plan