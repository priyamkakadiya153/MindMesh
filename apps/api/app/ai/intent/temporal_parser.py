import re
from typing import Optional
from app.ai.intent.models import TemporalConstraint

class TemporalParser:
    """
    Parses temporal expressions from user query strings.
    """

    TEMPORAL_PATTERNS = [
        (re.compile(r"\b(today)\b", re.IGNORECASE), 0, "day"),
        (re.compile(r"\b(yesterday)\b", re.IGNORECASE), -1, "day"),
        (re.compile(r"\b(tomorrow)\b", re.IGNORECASE), 1, "day"),
        (re.compile(r"\b(two days ago|2 days ago)\b", re.IGNORECASE), -2, "day"),
        (re.compile(r"\b(three days ago|3 days ago)\b", re.IGNORECASE), -3, "day"),
        (re.compile(r"\b(last week)\b", re.IGNORECASE), -7, "week"),
        (re.compile(r"\b(this week)\b", re.IGNORECASE), 0, "week"),
        (re.compile(r"\b(last month)\b", re.IGNORECASE), -30, "month"),
        (re.compile(r"\b(recently|lately)\b", re.IGNORECASE), -7, "week"),
    ]

    @classmethod
    def parse(cls, query: str) -> Optional[TemporalConstraint]:
        for pattern, rel_days, gran in cls.TEMPORAL_PATTERNS:
            m = pattern.search(query)
            if m:
                return TemporalConstraint(
                    raw_expression=m.group(0),
                    relative_days=rel_days,
                    granularity=gran
                )
        return None
