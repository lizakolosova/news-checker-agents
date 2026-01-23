"""LLM client for query planning."""

from __future__ import annotations

from typing import Optional, Any
import structlog

from news_fact_checker.research.constants import (
    LLM_TEMPERATURE,
    LLM_MODEL_GROQ,
    LLM_MODEL_OLLAMA,
)

logger = structlog.get_logger().bind(component="llm_client")


class LLMClient:

    def __init__(self, client: Any, temperature: float = LLM_TEMPERATURE):
        self.client = client
        self.temperature = temperature
        self._client_type = self._detect_client_type()

    def generate(self, prompt: str) -> str:
        if self._client_type == "groq":
            return self._call_groq(prompt)
        elif self._client_type == "ollama":
            return self._call_ollama(prompt)
        else:
            raise TypeError(f"Unsupported LLM client type: {type(self.client)}")

    def _detect_client_type(self) -> str:
        if hasattr(self.client, "chat") and hasattr(self.client.chat, "completions"):
            return "groq"
        elif hasattr(self.client, "chat"):
            return "ollama"
        else:
            return "unknown"

    def _call_groq(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=LLM_MODEL_GROQ,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("groq_call_failed", error=str(e))
            raise

    def _call_ollama(self, prompt: str) -> str:
        try:
            response = self.client.chat(
                model=LLM_MODEL_OLLAMA,
                messages=[{"role": "user", "content": prompt}],
            )

            message = response.get("message") or {}
            content = message.get("content", "")

            if not content:
                raise ValueError("Empty content from Ollama")

            return content
        except Exception as e:
            logger.error("ollama_call_failed", error=str(e))
            raise


def create_llm_client(client: Any, temperature: float = LLM_TEMPERATURE) -> Optional[LLMClient]:
    if client is None:
        return None

    try:
        return LLMClient(client, temperature)
    except Exception as e:
        logger.warning("llm_client_creation_failed", error=str(e))
        return None