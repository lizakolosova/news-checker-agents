from __future__ import annotations

import re

def assess_evidence_quality(
        claim: str,
    snippet: str = "",
    stance: str = "unclear",
) -> float:

    if stance not in {"supports", "refutes"}:
        return 0.35

    score = 0.5

    text = f"{claim} {snippet}".lower()

    numbers = re.findall(r"\b\d+(?:\.\d+)?\b", claim)
    if numbers:
        ev_nums = re.findall(r"\b\d+(?:\.\d+)?\b", text)

        def to_float(s: str) -> float:
            return float(s)

        compatible = False
        for cn in numbers:
            c_val = to_float(cn)
            for en in ev_nums:
                e_val = to_float(en)
                rel_diff = abs(c_val - e_val) / max(abs(e_val), 1.0)
                if rel_diff <= 0.15:
                    compatible = True
                    break
            if compatible:
                break

        if compatible:
            score += 0.25

    if len(snippet.strip()) < 40:
        score -= 0.15

    return max(0.0, min(1.0, score))


class QualityAssessor:
    def __init__(self, logger=None):
        self.logger = logger

