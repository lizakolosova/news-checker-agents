"""Regex patterns for claim detection."""

from __future__ import annotations

import re
from typing import Pattern


class ClaimPatterns:
    """Compiled regex patterns for efficient claim detection."""

    def __init__(self):
        self.number_pattern: Pattern = re.compile(
            r"\b\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:%|percent|million|billion|trillion|jobs))?\b",
            re.IGNORECASE,
        )

        self.date_pattern: Pattern = re.compile(
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
            re.IGNORECASE,
        )

        self.year_pattern: Pattern = re.compile(r"\b(19|20)\d{2}\b")

        self.temporal_marker_pattern: Pattern = re.compile(
            r"\b(?:in|during|on|by|from|to)\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\b|"
            r"\b(?:in|during|on|by|from|to)\s+\d{4}\b",
            re.IGNORECASE,
        )

        self.attribution_pattern: Pattern = re.compile(
            r"\b(?:according to|said|stated|reported|announced|claimed|noted|confirmed)\b",
            re.IGNORECASE,
        )

        self.comparative_pattern: Pattern = re.compile(
            r"\b(?:more than|less than|higher than|lower than|increased|decreased|rose|fell|drop(?:ped)?|surge(?:d)?|decline(?:d)?)\b",
            re.IGNORECASE,
        )

        self.causal_pattern: Pattern = re.compile(
            r"\b(?:because|due to|as a result|therefore|leading to|resulting in|caused by)\b",
            re.IGNORECASE,
        )

        _token = r"(?:[A-Z]{2,}(?:\.[A-Z]{2,})*|[A-Z][a-z]+)"
        self.entity_pattern: Pattern = re.compile(rf"\b{_token}(?:\s+{_token})*\b")

        self.relative_time_pattern: Pattern = re.compile(
            r"\b(?:yesterday|today|tomorrow|last\s+week|last\s+month|last\s+year|next\s+month|this\s+year)\b",
            re.IGNORECASE,
        )

        self.coordinating_conjunction: Pattern = re.compile(r"\s+(?:and|but|or)\s+", re.IGNORECASE)