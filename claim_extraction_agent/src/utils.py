"""Utility functions for claim extraction."""

import re
from typing import List

def segment_sentences(text: str) -> List[str]:
    """
    Segment text into sentences.

    Args:
        text: Input text

    Returns:
        List of sentences
    """
    # Handle common abbreviations
    text = re.sub(r'(?<=[A-Z])\.(?=[A-Z])', '|||', text)
    text = re.sub(r'(?<=Dr)\.', '|||', text)
    text = re.sub(r'(?<=Mr)\.', '|||', text)
    text = re.sub(r'(?<=Mrs)\.', '|||', text)
    text = re.sub(r'(?<=Ms)\.', '|||', text)

    sentences = re.split(r'[.!?]+\s+', text)
    sentences = [s.replace('|||', '.').strip() for s in sentences if s.strip()]

    return sentences


def clean_claim_text(text: str) -> str:
    """
    Clean and normalize claim text.

    Args:
        text: Input text

    Returns:
        Cleaned text
    """
    text = re.sub(r'\s+', ' ', text)

    text = text.strip()

    if not text.endswith(('.', '!', '?')):
        text += '.'

    return text


def get_context(sentences: List[str], idx: int, window: int = 1) -> str:
    """
    Get context sentences around a given index.

    Args:
        sentences: All sentences
        idx: Current sentence index
        window: Number of sentences before/after to include

    Returns:
        Context string
    """
    start = max(0, idx - window)
    end = min(len(sentences), idx + window + 1)
    return ' '.join(sentences[start:end])


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple text similarity ratio.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score between 0 and 1
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0