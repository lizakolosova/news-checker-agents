from __future__ import annotations

import re
from typing import List

from news_fact_checker.exceptions import SentenceSegmentationError

_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")

_ABBREVIATIONS = (
    "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Sr.", "Jr.", "St.",
    "vs.", "etc.", "e.g.", "i.e.", "U.S.", "U.K.", "E.U.",
    "No.", "Inc.", "Ltd.", "Co.", "Corp.", "Gov.", "Sen.", "Rep.",
)


def _protect(text: str) -> str:
    placeholder = "∯"
    text = re.sub(r"(?<=\d)\.(?=\d)", placeholder, text)
    text = re.sub(r"\b([A-Z])\.(?=\s*[A-Z]\b)", r"\1" + placeholder, text)
    for abbr in _ABBREVIATIONS:
        safe = abbr.replace(".", placeholder)
        text = text.replace(abbr, safe)
    return text


def _unprotect(text: str) -> str:
    return text.replace("∯", ".")


def segment_sentences(text: str) -> List[str]:
    if not text:
        return []

    try:
        t = re.sub(r"\s+", " ", text.strip())
        t = _protect(t)
        parts = _SENT_SPLIT_RE.split(t)
        sentences = []
        for p in parts:
            p = _unprotect(p).strip()
            if p:
                sentences.append(p)
        return sentences

    except Exception as e:
        raise SentenceSegmentationError(f"Failed to segment sentences: {e}") from e


def get_context(sentences: List[str], index: int, window: int = 2) -> str:
    if not sentences or index < 0 or index >= len(sentences):
        return ""

    start = max(0, index - window)
    end = min(len(sentences), index + window + 1)
    context_sentences = sentences[start:end]
    return " ".join(context_sentences)


def clean_claim_text(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text).strip()
    text = text.strip("\"'")
    text = re.sub(r"[\u2018\u2019]", "'", text)
    text = re.sub(r"[\u201c\u201d]", '"', text)

    if text and text[-1] not in ".!?":
        text += "."

    return text


def normalize_for_similarity(text: str) -> str:
    if not text:
        return ""

    t = text.lower()
    t = t.replace("%", " percent ")
    t = re.sub(r"[^a-z0-9\s']", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def tokenize(text: str) -> List[str]:
    t = normalize_for_similarity(text)
    return _WORD_RE.findall(t)


def calculate_text_similarity(text1: str, text2: str) -> float:
    tokens1 = set(tokenize(text1))
    tokens2 = set(tokenize(text2))

    if not tokens1 or not tokens2:
        return 0.0

    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    return intersection / union if union else 0.0


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = " ".join(text.split())
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()