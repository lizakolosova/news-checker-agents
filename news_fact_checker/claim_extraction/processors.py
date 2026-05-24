from __future__ import annotations

from typing import List

from news_fact_checker.claim_extraction.models import Claim
from news_fact_checker.claim_extraction import patterns
from news_fact_checker.claim_extraction.extractors import FeatureExtractor
from news_fact_checker.claim_extraction.validators import VerifiabilityAssessor
from news_fact_checker.utils import clean_claim_text, calculate_text_similarity
from news_fact_checker.claim_extraction.constants import (
    MIN_SUB_CLAIM_WORDS,
    SUB_CLAIM_CONFIDENCE_MULTIPLIER,
    DEFAULT_SIMILARITY_THRESHOLD,
)


class SubClaimProcessor:

    def __init__(
            self,
            min_words: int = MIN_SUB_CLAIM_WORDS,
            confidence_multiplier: float = SUB_CLAIM_CONFIDENCE_MULTIPLIER,
    ):
        self.min_words = min_words
        self.confidence_multiplier = confidence_multiplier
        self.feature_extractor = FeatureExtractor()
        self.verifiability_assessor = VerifiabilityAssessor()

    def extract_sub_claims(
            self,
            sentence: str,
            parent_claim: Claim
    ) -> List[Claim]:
        if not self._has_conjunctions(sentence):
            return []

        parts = patterns.COORDINATING_CONJUNCTION_PATTERN.split(sentence)

        if len(parts) <= 1:
            return []

        sub_claims: List[Claim] = []

        for part in parts[1:]:
            part = part.strip()

            if len(part.split()) <= self.min_words:
                continue

            ver_score, ver_reason = self.verifiability_assessor.assess(part)
            if not self.verifiability_assessor.is_verifiable(part):
                continue

            features = self.feature_extractor.extract_all(part)

            sub_claim = Claim(
                text=clean_claim_text(part),
                claim_type=parent_claim.claim_type,
                confidence=parent_claim.confidence * self.confidence_multiplier,
                context=parent_claim.context,
                source_sentence=sentence,
                entities=features["entities"],
                temporal_markers=features["temporal_markers"],
                numerical_data=features["numerical_data"],
                metadata={
                    **(parent_claim.metadata or {}),
                    "is_sub_claim": True,
                    "verifiability_score": round(ver_score, 3),
                    "verifiability_reason": ver_reason,
                },
            )

            sub_claims.append(sub_claim)

        return sub_claims

    @staticmethod
    def _has_conjunctions(sentence: str) -> bool:
        return "," in sentence or ";" in sentence


class ClaimDeduplicator:

    def __init__(self, similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD):
        self.similarity_threshold = similarity_threshold

    def deduplicate(self, claims: List[Claim]) -> List[Claim]:
        if not claims:
            return []

        sorted_claims = sorted(claims, key=lambda x: x.confidence, reverse=True)

        unique_claims: List[Claim] = []
        seen_texts = set()

        for claim in sorted_claims:
            normalized_text = (claim.text or "").lower().strip()

            if normalized_text in seen_texts:
                continue

            if self._is_duplicate(claim, unique_claims):
                continue

            unique_claims.append(claim)
            seen_texts.add(normalized_text)

        return unique_claims

    def _is_duplicate(self, claim: Claim, existing_claims: List[Claim]) -> bool:
        for existing in existing_claims:
            similarity = calculate_text_similarity(claim.text, existing.text)
            if similarity > self.similarity_threshold:
                return True
        return False

    def get_duplicates(self, claims: List[Claim]) -> List[List[Claim]]:
        if not claims:
            return []

        duplicate_groups: List[List[Claim]] = []
        processed = set()

        for i, claim in enumerate(claims):
            if i in processed:
                continue

            group = [claim]
            for j, other in enumerate(claims[i + 1:], start=i + 1):
                if j in processed:
                    continue

                similarity = calculate_text_similarity(claim.text, other.text)
                if similarity > self.similarity_threshold:
                    group.append(other)
                    processed.add(j)

            if len(group) > 1:
                duplicate_groups.append(group)

            processed.add(i)

        return duplicate_groups