"""Main Claim Extraction Agent."""

from __future__ import annotations

import re
import uuid
from typing import List, Optional, Dict, Any, Tuple

import structlog

from news_fact_checker.config import ClaimExtractionConfig, DEFAULT_CONFIG
from news_fact_checker.claim_extraction.extractors import EntityExtractor, TemporalExtractor, NumberExtractor
from news_fact_checker.claim_extraction.models import Claim, ClaimType
from news_fact_checker.claim_extraction.patterns import ClaimPatterns
from news_fact_checker.utils import (
    get_context,
    segment_sentences,
    clean_claim_text,
    calculate_text_similarity,
)

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
    """
    Extracts verifiable factual claims from news articles.
    Dependency-light, heuristic-based extraction with verifiability gating.
    """

    def __init__(self, config: Optional[ClaimExtractionConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.logger = structlog.get_logger().bind(component="news_fact_checker")

        self.patterns = ClaimPatterns()
        self.entity_extractor = EntityExtractor(self.patterns)
        self.temporal_extractor = TemporalExtractor(self.patterns)
        self.number_extractor = NumberExtractor(self.patterns)

    def extract_claims(
        self,
        article_text: str,
        article_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Claim]:
        trace_id = str(uuid.uuid4())
        self.logger.info(
            "claim_extraction_started",
            trace_id=trace_id,
            article_length=len(article_text or ""),
        )

        try:
            sentences = segment_sentences(article_text or "")
            claims: List[Claim] = []

            for idx, sentence in enumerate(sentences):
                claims.extend(
                    self._extract_from_sentence(
                        sentence=sentence,
                        all_sentences=sentences,
                        sentence_idx=idx,
                        metadata=article_metadata,
                    )
                )

            filtered = [c for c in claims if c.confidence >= self.config.min_confidence]
            unique_claims = self._deduplicate_claims(filtered)

            self.logger.info(
                "claim_extraction_completed",
                trace_id=trace_id,
                total_claims=len(unique_claims),
                high_confidence=sum(1 for c in unique_claims if c.confidence > 0.8),
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
            raise

    def _extract_from_sentence(
        self,
        sentence: str,
        all_sentences: List[str],
        sentence_idx: int,
        metadata: Optional[Dict[str, Any]],
    ) -> List[Claim]:
        claim_type, confidence = self._classify_sentence(sentence)
        if confidence < 0.3:
            return []

        context = get_context(all_sentences, sentence_idx, self.config.context_window)

        entities = self.entity_extractor.extract(sentence)
        temporal_markers = self.temporal_extractor.extract(sentence)
        numerical_data = self.number_extractor.extract(sentence)

        ver_score, ver_reason = self._assess_verifiability(sentence)
        if self._should_drop_unverifiable(ver_score):
            return []

        claim = Claim(
            text=clean_claim_text(sentence),
            claim_type=claim_type,
            confidence=confidence,
            context=context,
            source_sentence=sentence,
            entities=entities,
            temporal_markers=temporal_markers,
            numerical_data=numerical_data,
            metadata={
                **(metadata or {}),
                "verifiability_score": round(ver_score, 3),
                "verifiability_reason": ver_reason,
            },
        )

        claims: List[Claim] = [claim]

        if "," in sentence or ";" in sentence:
            claims.extend(self._extract_sub_claims(sentence, claim))

        return claims

    def _assess_verifiability(self, sentence: str) -> Tuple[float, str]:
        """
        Returns (verifiability_score, reason). Higher is better.

        Generic anchors:
          - number, date, named entity/org, explicit attribution, or actual quotation marks
        Drops vague referent starters with no anchors.
        Penalizes hedges and intensifiers without metric/attribution.
        """
        s = (sentence or "").strip()
        s_lower = s.lower()

        has_number = bool(self.patterns.number_pattern.search(s))
        has_date = bool(self.patterns.date_pattern.search(s))
        has_entity = bool(self.patterns.entity_pattern.search(s))
        has_attrib = bool(self.patterns.attribution_pattern.search(s))

        has_quote = ('"' in s) or ("“" in s) or ("”" in s)

        anchors = sum([has_number, has_date, has_entity, has_attrib, has_quote])

        if getattr(self.config, "drop_vague_referents", True):
            vague_starters = tuple(
                getattr(
                    self.config,
                    "vague_referents",
                    ("this", "that", "these", "those", "it", "they", "there", "such"),
                )
            )
            if s_lower.startswith(vague_starters) and anchors == 0:
                return 0.0, "vague_referent_no_anchor"

        tokens = set(re.findall(r"[a-z]+", s_lower))

        intensifiers = {"significant", "dramatic", "remarkable", "substantial", "huge", "massive", "major", "sharp"}
        if tokens.intersection(intensifiers) and not (has_number or has_date) and not has_attrib:
            return 0.2, "intensifier_without_metric_or_attribution"

        if anchors == 0:
            return 0.1, "no_verification_anchor"

        score = min(1.0, 0.25 + 0.2 * anchors)

        hedges = {"may", "might", "could", "possibly", "perhaps", "appears", "seems", "reportedly", "allegedly"}
        if tokens.intersection(hedges):
            score = max(0.0, score - 0.15)

        return score, "ok"

    def _should_drop_unverifiable(self, ver_score: float) -> bool:
        return bool(
            getattr(self.config, "drop_unverifiable", True)
            and ver_score < getattr(self.config, "min_verifiability", 0.35)
        )

    def _classify_sentence(self, sentence: str) -> Tuple[ClaimType, float]:
        """
        Classify sentence type with precedence rules and assign confidence.
        Precedence (highest → lowest):
          ATTRIBUTION → STATISTICAL → TEMPORAL → CAUSAL → COMPARATIVE → FACTUAL
        """
        s = (sentence or "").lower()
        confidence = 0.4

        has_number = bool(self.patterns.number_pattern.search(sentence))
        has_date = bool(self.patterns.date_pattern.search(sentence))
        has_attribution = bool(self.patterns.attribution_pattern.search(sentence))
        has_causal = bool(self.patterns.causal_pattern.search(sentence))
        has_comparative = bool(self.patterns.comparative_pattern.search(sentence))

        if has_attribution:
            claim_type = ClaimType.ATTRIBUTION
            confidence += 0.35
        elif has_number:
            claim_type = ClaimType.STATISTICAL
            confidence += 0.3
        elif has_date:
            claim_type = ClaimType.TEMPORAL
            confidence += 0.25
        elif has_causal:
            claim_type = ClaimType.CAUSAL
            confidence += 0.2
        elif has_comparative:
            claim_type = ClaimType.COMPARATIVE
            confidence += 0.2
        else:
            claim_type = ClaimType.FACTUAL
            confidence += 0.1

        opinion_markers = {"may", "might", "could", "possibly", "perhaps", "seems"}
        if any(m in s.split() for m in opinion_markers):
            confidence -= 0.2

        definitive_markers = {"is", "are", "was", "were", "has", "have"}
        if any(m in s.split() for m in definitive_markers):
            confidence += 0.1

        confidence = max(0.0, min(1.0, confidence))
        return claim_type, confidence

    def _extract_sub_claims(self, sentence: str, parent_claim: Claim) -> List[Claim]:
        """Extract sub-claims from compound sentences split by coordinating conjunctions."""
        parts = self.patterns.coordinating_conjunction.split(sentence)
        if len(parts) <= 1:
            return []

        sub_claims: List[Claim] = []
        for part in parts[1:]:
            part = part.strip()
            if len(part.split()) <= self.config.min_sub_claim_words:
                continue

            sub_ver_score, sub_ver_reason = self._assess_verifiability(part)
            if self._should_drop_unverifiable(sub_ver_score):
                continue

            sub_claims.append(
                Claim(
                    text=clean_claim_text(part),
                    claim_type=parent_claim.claim_type,
                    confidence=parent_claim.confidence * self.config.sub_claim_confidence_multiplier,
                    context=parent_claim.context,
                    source_sentence=sentence,
                    entities=self.entity_extractor.extract(part),
                    temporal_markers=self.temporal_extractor.extract(part),
                    numerical_data=self.number_extractor.extract(part),
                    metadata={
                        **(parent_claim.metadata or {}),
                        "is_sub_claim": True,
                        "verifiability_score": round(sub_ver_score, 3),
                        "verifiability_reason": sub_ver_reason,
                    },
                )
            )

        return sub_claims

    def _deduplicate_claims(self, claims: List[Claim]) -> List[Claim]:
        """Remove duplicate or very similar claims (keeps highest-confidence versions)."""
        if not claims:
            return []

        unique_claims: List[Claim] = []
        seen_texts = set()

        for claim in sorted(claims, key=lambda x: x.confidence, reverse=True):
            normalized_text = (claim.text or "").lower().strip()
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