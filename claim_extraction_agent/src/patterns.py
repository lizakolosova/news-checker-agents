"""Regex patterns for claim detection."""

import re
from typing import Pattern


class ClaimPatterns:
    """Compiled regex patterns for efficient claim detection."""

    def __init__(self):
        """Initialize and compile all patterns."""
        self.number_pattern: Pattern = re.compile(
            r'\b\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:%|percent|million|billion|trillion))?\b',
            re.IGNORECASE
        )

        self.date_pattern: Pattern = re.compile(
            r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|'
            r'(?:January|February|March|April|May|June|July|August|September|'
            r'October|November|December)\s+\d{1,2},?\s+\d{4}|'
            r'\d{4})\b',
            re.IGNORECASE
        )

        self.attribution_pattern: Pattern = re.compile(
            r'(?:said|stated|claimed|announced|reported|according to|told)\s+',
            re.IGNORECASE
        )

        self.causal_pattern: Pattern = re.compile(
            r'\b(?:caused|because|due to|as a result|led to|resulted in)\b',
            re.IGNORECASE
        )

        self.comparative_pattern: Pattern = re.compile(
            r'\b(?:more than|less than|higher than|lower than|compared to|versus|vs)\b',
            re.IGNORECASE
        )

        self.entity_pattern: Pattern = re.compile(
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        )

        self.relative_time_pattern: Pattern = re.compile(
            r'\b(?:yesterday|today|tomorrow|last week|next month|this year)\b',
            re.IGNORECASE
        )

        self.coordinating_conjunction: Pattern = re.compile(
            r'\s+(?:and|but|or)\s+'
        )