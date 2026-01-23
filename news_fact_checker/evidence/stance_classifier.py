from dataclasses import dataclass
from typing import Set
import re
import structlog

logger = structlog.get_logger().bind(component="stance_classifier")


@dataclass
class StanceResult:
    label: str
    confidence: float
    reason: str
    source: str


_SUPPORT_CUES = {
    "confirms", "confirmed", "showed", "shows", "found", "finds",
    "rose to", "fell to", "increased to", "decreased to", "was", "were",
    "reached", "up to", "down to", "remained at", "unchanged at",
    "according to", "reported", "announced", "stated", "data shows",
    "statistics show", "grossed", "earned", "box office", "scored",
    "won", "defeated", "beat",
}

_REFUTE_CUES = {
    "false", "falsely", "debunked", "debunks", "incorrect", "wrong",
    "misleading", "no evidence", "denied", "deny", "denies", "did not",
    "didn't", "has not", "haven't", "never happened", "contradicts",
    "disputed", "disputes",
}


def _extract_numbers(text: str) -> Set[str]:
    return set(re.findall(r"\b\d+(?:\.\d+)?%?\b", text))


def _numbers_compatible(claim: str, evidence: str) -> bool:
    claim_nums = _extract_numbers(claim)
    if not claim_nums:
        return True

    ev_nums = _extract_numbers(evidence)
    if not ev_nums:
        return False

    def to_float(s: str) -> float:
        return float(s.rstrip("%"))

    for cn in claim_nums:
        c_val = to_float(cn)
        for en in ev_nums:
            e_val = to_float(en)
            if e_val == 0:
                continue
            rel_diff = abs(c_val - e_val) / max(abs(e_val), 1.0)
            if rel_diff <= 0.15:
                return True

    return False


def _extract_key_terms(text: str, min_length: int = 4) -> Set[str]:
    words = re.findall(r"[a-z]{" + str(min_length) + r",}", text.lower())
    return set(words)


def deterministic_stance_classification( claim_text: str, snippet: str,source_url: str = "", source_title: str = "",) -> StanceResult:
    if not claim_text or not snippet:
        return StanceResult(  label="unclear", confidence=0.3,reason="Insufficient text for classification.",
            source="deterministic",)

    claim_lower = claim_text.lower()
    evidence_text = f"{source_title or ''} {snippet or ''}".lower()

    if any(cue in evidence_text for cue in _REFUTE_CUES):
        return StanceResult(  label="refutes", confidence=0.8, reason="Evidence uses explicit refutation/denial language.",
            source="deterministic", )

    if not _numbers_compatible(claim_lower, evidence_text):
        return StanceResult(label="unclear", confidence=0.55, reason="Numbers/dates in evidence differ substantially from the claim.",
            source="deterministic",)

    has_support_cues = any(cue in evidence_text for cue in _SUPPORT_CUES)
    claim_terms = _extract_key_terms(claim_lower, min_length=4)
    evidence_terms = _extract_key_terms(evidence_text, min_length=4)
    common_terms = claim_terms & evidence_terms
    term_overlap_ratio = len(common_terms) / len(claim_terms) if claim_terms else 0.0
    has_term_overlap = len(common_terms) >= 2 or term_overlap_ratio >= 0.3

    if has_support_cues and has_term_overlap:
        return StanceResult( label="supports",confidence=0.75,reason="Evidence language and key terms align with the claim.",
            source="deterministic",)

    return StanceResult( label="unclear", confidence=0.55, reason="Evidence is not explicit enough to support or refute.",
        source="deterministic", )