from __future__ import annotations

from typing import List, Dict
import requests
import structlog

from news_fact_checker.research.models import SearchResult
from news_fact_checker.research.constants import (
    SEARCH_TIMEOUT_SECONDS,
    SERPER_ENDPOINT,
    TITLE_MAX_LENGTH,
    SNIPPET_DISPLAY_MAX_LENGTH,
)

logger = structlog.get_logger().bind(component="search_client")


class SearchClient:

    def __init__(self, api_key: str, timeout: int = SEARCH_TIMEOUT_SECONDS):
        self.api_key = api_key
        self.timeout = timeout
        self.endpoint = SERPER_ENDPOINT

    def search(
            self,
            queries: List[str],
            per_query_results: int = 5
    ) -> List[SearchResult]:
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

        all_results: List[SearchResult] = []

        for query in queries:
            query = (query or "").strip()
            if not query:
                continue

            payload = {
                "q": query,
                "num": per_query_results,
                "autocorrect": True,
                "hl": "en",
            }

            try:
                response = requests.post(
                    self.endpoint,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                data = response.json()
                results = self._extract_results(data)
                all_results.extend(results)

            except requests.HTTPError as e:
                logger.warning(
                    "search_http_error",
                    query=query,
                    status_code=response.status_code,
                    error=str(e),
                )
                continue
            except Exception as e:
                logger.warning(
                    "search_error",
                    query=query,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                continue

        return self._deduplicate(all_results)

    def _extract_results(self, data: Dict) -> List[SearchResult]:
        results: List[SearchResult] = []

        organic = data.get("organic", []) or []
        news = data.get("news", []) or []

        for item in organic:
            result = self._create_result(item, "organic")
            if result:
                results.append(result)

        for item in news:
            result = self._create_result(item, "news")
            if result:
                results.append(result)

        answer_box = data.get("answerBox") or {}
        if isinstance(answer_box, dict) and (answer_box.get("link") or answer_box.get("title")):
            result = self._create_result(answer_box, "answerBox")
            if result:
                results.append(result)

        kg = data.get("knowledgeGraph") or {}
        if isinstance(kg, dict) and (kg.get("link") or kg.get("title")):
            result = self._create_result(kg, "knowledgeGraph")
            if result:
                results.append(result)

        return results

    def _create_result(self, item: Dict, kind: str) -> Optional[SearchResult]:
        url = item.get("link") or item.get("url") or ""
        if not url:
            return None

        title = (item.get("title") or "")[:TITLE_MAX_LENGTH]
        snippet = (item.get("snippet") or item.get("snippetHighlighted") or "")[:SNIPPET_DISPLAY_MAX_LENGTH]

        return SearchResult(
            url=url,
            title=title,
            snippet=snippet,
            kind=kind,
        )

    def _deduplicate(self, results: List[SearchResult]) -> List[SearchResult]:
        seen = set()
        unique: List[SearchResult] = []

        for result in results:
            url = result.get("url", "")
            if url and url not in seen:
                unique.append(result)
                seen.add(url)

        return unique