from __future__ import annotations

import re
from typing import Pattern


NUMBER_PATTERN: Pattern = re.compile(
    r"\b\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:%|percent|million|billion|trillion|jobs))?\b",
    re.IGNORECASE,
)

DATE_PATTERN: Pattern = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
    re.IGNORECASE,
)

YEAR_PATTERN: Pattern = re.compile(r"\b(19|20)\d{2}\b")

TEMPORAL_MARKER_PATTERN: Pattern = re.compile(
    r"\b(?:in|during|on|by|from|to)\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\b|"
    r"\b(?:in|during|on|by|from|to)\s+\d{4}\b",
    re.IGNORECASE,
)

ATTRIBUTION_PATTERN: Pattern = re.compile(
    r"\b(?:according to|said|stated|reported|announced|claimed|noted|confirmed|told|revealed|disclosed)\b",
    re.IGNORECASE,
)

COMPARATIVE_PATTERN: Pattern = re.compile(
    r"\b(?:more than|less than|higher than|lower than|increased|decreased|rose|fell|drop(?:ped)?|surge(?:d)?|decline(?:d)?|compared to|versus)\b",
    re.IGNORECASE,
)

CAUSAL_PATTERN: Pattern = re.compile(
    r"\b(?:because|due to|as a result|therefore|leading to|resulting in|caused by|leads to|results in)\b",
    re.IGNORECASE,
)

_TOKEN = r"(?:[A-Z]{2,}(?:\.[A-Z]{2,})*|[A-Z][a-z]+)"
ENTITY_PATTERN: Pattern = re.compile(rf"\b{_TOKEN}(?:\s+{_TOKEN})*\b")

RELATIVE_TIME_PATTERN: Pattern = re.compile(
    r"\b(?:yesterday|today|tomorrow|last\s+week|last\s+month|last\s+year|next\s+month|this\s+year|this\s+week|next\s+week)\b",
    re.IGNORECASE,
)

COORDINATING_CONJUNCTION_PATTERN: Pattern = re.compile(
    r"\s+(?:and|but|or)\s+",
    re.IGNORECASE
)

QUOTE_PATTERN: Pattern = re.compile(
    r'"[^"]*"|"[^"]*"|\'[^\']*\'',
    re.IGNORECASE
)