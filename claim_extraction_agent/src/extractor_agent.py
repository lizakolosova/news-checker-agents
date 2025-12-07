"""Main Claim Extraction Agent."""

import uuid
import structlog
from typing import List, Optional, Dict, Any, Tuple

from models import Claim, ClaimType
from patterns import ClaimPatterns
from extractors import EntityExtractor, TemporalExtractor, NumericalExtractor
from utils import (
    segment_sentences,
    clean_claim_text,
    get_context,
    calculate_text_similarity
)
from config import ClaimExtractionConfig, DEFAULT_CONFIG

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


class ClaimExtractionAgent:
    """
    Advanced Claim Extraction Agent that identifies and extracts
    verifiable factual claims from news articles.
    """

    def __init__(self, config: Optional[ClaimExtractionConfig] = None):
        """
        Initialize the Claim Extraction Agent.

        Args:
            config: Configuration object (uses default if None)
        """
        self.config = config or DEFAULT_CONFIG
        self.logger = structlog.get_logger().bind(component="claim_extraction_agent")

        self.patterns = ClaimPatterns()
        self.entity_extractor = EntityExtractor(self.patterns)
        self.temporal_extractor = TemporalExtractor(self.patterns)
        self.numerical_extractor = NumericalExtractor(self.patterns)

    def extract_claims(
            self,
            article_text: str,
            article_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Claim]:
        """
        Extract verifiable claims from article text.

        Args:
            article_text: The full text of the news article
            article_metadata: Optional metadata about the article

        Returns:
            List of extracted Claim objects
        """
        trace_id = str(uuid.uuid4())
        self.logger.info(
            "claim_extraction_started",
            trace_id=trace_id,
            article_length=len(article_text)
        )

        try:
            sentences = segment_sentences(article_text)

            claims = []
            for idx, sentence in enumerate(sentences):
                extracted_claims = self._extract_from_sentence(
                    sentence,
                    sentences,
                    idx,
                    article_metadata
                )
                claims.extend(extracted_claims)

            filtered_claims = [
                claim for claim in claims
                if claim.confidence >= self.config.min_confidence
            ]

            unique_claims = self._deduplicate_claims(filtered_claims)

            self.logger.info(
                "claim_extraction_completed",
                trace_id=trace_id,
                total_claims=len(unique_claims),
                high_confidence=sum(
                    1 for c in unique_claims
                    if c.confidence > 0.8
                )
            )

            return unique_claims

        except Exception as e:
            self.logger.error(
                "claim_extraction_failed",
                trace_id=trace_id,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
            raise

    def _extract_from_sentence(
            self,
            sentence: str,
            all_sentences: List[str],
            sentence_idx: int,
            metadata: Optional[Dict[str, Any]]
    ) -> List[Claim]:
        """
        Extract claims from a single sentence.

        Args:
            sentence: The sentence to analyze
            all_sentences: All sentences for context
            sentence_idx: Index of current sentence
            metadata: Article metadata

        Returns:
            List of extracted claims
        """
        claims = []

        claim_type, confidence = self._classify_sentence(sentence)

        if confidence < 0.3:
            return claims

        context = get_context(
            all_sentences,
            sentence_idx,
            self.config.context_window
        )

        entities = self.entity_extractor.extract(sentence)
        temporal_markers = self.temporal_extractor.extract(sentence)
        numerical_data = self.numerical_extractor.extract(sentence)

        claim = Claim(
            text=clean_claim_text(sentence),
            claim_type=claim_type,
            confidence=confidence,
            context=context,
            source_sentence=sentence,
            entities=entities,
            temporal_markers=temporal_markers,
            numerical_data=numerical_data,
            metadata=metadata or {}
        )

        claims.append(claim)

        if ',' in sentence or ';' in sentence:
            sub_claims = self._extract_sub_claims(sentence, claim)
            claims.extend(sub_claims)

        return claims

    def _classify_sentence(self, sentence: str) -> Tuple[ClaimType, float]:
        """
        Classify sentence type and assign confidence score.

        Args:
            sentence: Input sentence

        Returns:
            Tuple of (ClaimType, confidence_score)
        """
        confidence = 0.5
        claim_type = ClaimType.FACTUAL

        if self.patterns.number_pattern.search(sentence):
            claim_type = ClaimType.STATISTICAL
            confidence += 0.2

        if self.patterns.date_pattern.search(sentence):
            if claim_type == ClaimType.STATISTICAL:
                confidence += 0.1
            else:
                claim_type = ClaimType.TEMPORAL
                confidence += 0.15

        if self.patterns.attribution_pattern.search(sentence):
            claim_type = ClaimType.ATTRIBUTION
            confidence += 0.25

        if self.patterns.causal_pattern.search(sentence):
            claim_type = ClaimType.CAUSAL
            confidence += 0.15

        if self.patterns.comparative_pattern.search(sentence):
            claim_type = ClaimType.COMPARATIVE
            confidence += 0.15

        opinion_markers = ['may', 'might', 'could', 'possibly', 'perhaps', 'seems']
        if any(marker in sentence.lower() for marker in opinion_markers):
            confidence -= 0.2

        definitive_markers = ['is', 'are', 'was', 'were', 'has', 'have']
        if any(marker in sentence.lower().split() for marker in definitive_markers):
            confidence += 0.1

        confidence = max(0.0, min(1.0, confidence))

        return claim_type, confidence

    def _extract_sub_claims(self, sentence: str, parent_claim: Claim) -> List[Claim]:
        """
        Extract sub-claims from complex sentences.

        Args:
            sentence: Input sentence
            parent_claim: Parent claim object

        Returns:
            List of sub-claims
        """
        sub_claims = []

        parts = self.patterns.coordinating_conjunction.split(sentence)

        if len(parts) > 1:
            for part in parts[1:]:
                if len(part.split()) > self.config.min_sub_claim_words:
                    sub_claim = Claim(
                        text=clean_claim_text(part),
                        claim_type=parent_claim.claim_type,
                        confidence=parent_claim.confidence * self.config.sub_claim_confidence_multiplier,
                        context=parent_claim.context,
                        source_sentence=sentence,
                        entities=self.entity_extractor.extract(part),
                        temporal_markers=self.temporal_extractor.extract(part),
                        numerical_data=self.numerical_extractor.extract(part),
                        metadata={**parent_claim.metadata, 'is_sub_claim': True}
                    )
                    sub_claims.append(sub_claim)

        return sub_claims

    def _deduplicate_claims(self, claims: List[Claim]) -> List[Claim]:
        """
        Remove duplicate or very similar claims.

        Args:
            claims: List of claims

        Returns:
            Deduplicated list of claims
        """
        if not claims:
            return claims

        unique_claims = []
        seen_texts = set()

        for claim in sorted(claims, key=lambda x: x.confidence, reverse=True):
            normalized_text = claim.text.lower().strip()
            if normalized_text in seen_texts:
                continue

            is_duplicate = False
            for existing in unique_claims:
                similarity = calculate_text_similarity(claim.text, existing.text)
                if similarity > self.config.similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_claims.append(claim)
                seen_texts.add(normalized_text)

        return unique_claims
