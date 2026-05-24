from __future__ import annotations

import uuid
from typing import List, Optional

import structlog

from news_fact_checker.config import ClaimExtractionConfig, DEFAULT_CONFIG
from news_fact_checker.claim_extraction.models import Claim, ExtractionResult, ArticleMetadata
from news_fact_checker.claim_extraction.extractors import FeatureExtractor
from news_fact_checker.claim_extraction.classifiers import ClaimClassifier
from news_fact_checker.claim_extraction.validators import VerifiabilityAssessor
from news_fact_checker.claim_extraction.processors import SubClaimProcessor, ClaimDeduplicator
from news_fact_checker.utils import get_context, segment_sentences, clean_claim_text
from news_fact_checker.exceptions import ClaimExtractionError

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


class ClaimExtractionAgent:
    def __init__(self, config: Optional[ClaimExtractionConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.logger = structlog.get_logger().bind(component="claim_extraction_agent")

        self.classifier = ClaimClassifier()
        self.verifiability_assessor = VerifiabilityAssessor(
            min_score=self.config.min_verifiability,
            drop_vague_referents=self.config.drop_vague_referents,
        )
        self.feature_extractor = FeatureExtractor()
        self.sub_claim_processor = SubClaimProcessor(
            min_words=self.config.min_sub_claim_words,
            confidence_multiplier=self.config.sub_claim_confidence_multiplier,
        )
        self.deduplicator = ClaimDeduplicator(
            similarity_threshold=self.config.similarity_threshold
        )

    def extract_claims(
            self,
            article_text: str,
            article_metadata: Optional[ArticleMetadata] = None,
    ) -> List[Claim]:
        trace_id = str(uuid.uuid4())
        self.logger.info(
            "claim_extraction_started",
            trace_id=trace_id,
            article_length=len(article_text or ""),
        )

        try:
            sentences = segment_sentences(article_text or "")

            if not sentences:
                self.logger.warning("no_sentences_found", trace_id=trace_id)
                return []

            all_claims: List[Claim] = []
            for idx, sentence in enumerate(sentences):
                sentence_claims = self._extract_from_sentence(
                    sentence=sentence,
                    all_sentences=sentences,
                    sentence_idx=idx,
                    metadata=article_metadata,
                )
                all_claims.extend(sentence_claims)

            filtered_claims = [
                claim for claim in all_claims
                if claim.confidence >= self.config.min_confidence
            ]

            unique_claims = self.deduplicator.deduplicate(filtered_claims)

            self.logger.info(
                "claim_extraction_completed",
                trace_id=trace_id,
                total_claims=len(unique_claims),
                high_confidence=sum(1 for c in unique_claims if c.is_high_confidence),
                sentences_processed=len(sentences),
            )

            return unique_claims

        except Exception as e:
            self.logger.error(
                "claim_extraction_failed",
                trace_id=trace_id,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True,
            )
            raise ClaimExtractionError(f"Claim extraction failed: {e}") from e

    def extract_with_metadata(
            self,
            article_text: str,
            article_metadata: Optional[ArticleMetadata] = None,
    ) -> ExtractionResult:
        sentences = segment_sentences(article_text or "")
        claims = self.extract_claims(article_text, article_metadata)

        return ExtractionResult(
            claims=claims,
            total_sentences=len(sentences),
            total_claims_extracted=len(claims),
            high_confidence_claims=sum(1 for c in claims if c.is_high_confidence),
            article_metadata=article_metadata,
            extraction_metadata={
                "config": {
                    "min_confidence": self.config.min_confidence,
                    "min_verifiability": self.config.min_verifiability,
                    "similarity_threshold": self.config.similarity_threshold,
                }
            },
        )

    def _extract_from_sentence(
            self,
            sentence: str,
            all_sentences: List[str],
            sentence_idx: int,
            metadata: Optional[ArticleMetadata],
    ) -> List[Claim]:
        claim_type, confidence = self.classifier.classify(sentence)

        if confidence < 0.3:
            return []

        ver_score, ver_reason = self.verifiability_assessor.assess(sentence)

        if self.config.drop_unverifiable and not self.verifiability_assessor.is_verifiable(sentence):
            return []

        context = get_context(all_sentences, sentence_idx, self.config.context_window)

        features = self.feature_extractor.extract_all(sentence)

        main_claim = Claim(
            text=clean_claim_text(sentence),
            claim_type=claim_type,
            confidence=confidence,
            context=context,
            source_sentence=sentence,
            entities=features["entities"],
            temporal_markers=features["temporal_markers"],
            numerical_data=features["numerical_data"],
            metadata={
                **(metadata or {}),
                "verifiability_score": round(ver_score, 3),
                "verifiability_reason": ver_reason,
                "sentence_index": sentence_idx,
            },
        )

        claims: List[Claim] = [main_claim]

        sub_claims = self.sub_claim_processor.extract_sub_claims(sentence, main_claim)
        claims.extend(sub_claims)

        return claims