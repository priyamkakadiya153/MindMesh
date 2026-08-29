import re
from typing import List, Dict, Any, Optional

class FollowUpDetector:
    """
    Detects whether a user query is a follow-up to previous conversation context.
    """

    FOLLOWUP_PHRASES = [
        re.compile(r"^\s*(why|how|who|when|where|what about|and|also|tell me more|more details)\??\s*$", re.IGNORECASE),
        re.compile(r"\b(the first one|the second one|the previous|it|this|that|those|these)\b", re.IGNORECASE),
        re.compile(r"^\s*what about (the first|the second|the last|it|this|that)\??\s*$", re.IGNORECASE)
    ]

    @classmethod
    def is_followup(cls, query: str, history: Optional[List[Dict[str, Any]]] = None) -> bool:
        if not history:
            return False

        q_clean = query.strip().lower()

        # Very short queries (<= 3 words) in active conversation are often follow-ups
        if len(q_clean.split()) <= 3 and any(q_clean.startswith(w) for w in ["why", "who", "how", "what", "and"]):
            return True

        for pat in cls.FOLLOWUP_PHRASES:
            if pat.search(q_clean):
                return True

        return False
