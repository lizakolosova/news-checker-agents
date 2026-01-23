from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict
import requests


@dataclass
class SerperClient:
    api_key: str
    timeout_s: int = 15
    endpoint: str = "https://google.serper.dev/search"

    def search(self, queries: List[str], per_query_results: int = 5) -> List[Dict[str, str]]:
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

        all_sources: List[Dict[str, str]] = []

        for q in queries:
            q = (q or "").strip()
            if not q:
                continue

            payload = {
                "q": q,
                "num": per_query_results,
                "autocorrect": True,
                "hl": "en",
            }

            try:
                resp = requests.post(
                    self.endpoint,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout_s,
                )
                resp.raise_for_status()
            except requests.HTTPError as e:
                try:
                    body = resp.text
                except Exception:
                    body = "<no body>"
                print(
                    f"[SerperClient] HTTP error for query={q!r}: {e} "
                    f"(status={resp.status_code}, body={body})"
                )
                continue

            data = resp.json()

            organic = data.get("organic", []) or []
            news = data.get("news", []) or []

            def push_result(r: Dict, kind: str = "organic") -> None:
                all_sources.append(
                    {
                        "url": r.get("link") or r.get("url") or "",
                        "title": (r.get("title") or "")[:160],
                        "snippet": (r.get("snippet") or r.get("snippetHighlighted") or "")[:1200],
                        "kind": kind,
                    }
                )

            for r in organic:
                push_result(r, "organic")

            for r in news:
                push_result(r, "news")

            answer_box = data.get("answerBox") or {}
            if isinstance(answer_box, dict) and answer_box.get("link") or answer_box.get("title"):
                push_result(answer_box, "answerBox")

            kg = data.get("knowledgeGraph") or {}
            if isinstance(kg, dict) and kg.get("link") or kg.get("title"):
                push_result(kg, "knowledgeGraph")

        seen = set()
        unique: List[Dict[str, str]] = []
        for s in all_sources:
            u = s.get("url", "")
            if u and u not in seen:
                unique.append(s)
                seen.add(u)

        return unique
