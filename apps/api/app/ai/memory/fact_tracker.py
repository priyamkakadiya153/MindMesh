import re
import time
from typing import List, Dict, Any, Tuple
from app.ai.memory.context_models import ConversationFact, FactType, FactStatus

class FactTracker:
    """
    Extracted Conversation Fact Tracker.
    Manages USER_STATED vs INFERRED facts, fact corrections, preferences, and deadlines.
    """

    DEADLINE_PATTERN = re.compile(r"\bdeadline (is|changed to|set to|moved to) (friday|monday|tuesday|wednesday|thursday|saturday|sunday|[a-z0-9\s,]+)", re.IGNORECASE)
    PREFERENCE_PATTERNS = [
        (re.compile(r"\b(keep answers short|be concise|short answers)\b", re.IGNORECASE), "verbosity", "concise"),
        (re.compile(r"\b(explain in detail|detailed answers|give me everything)\b", re.IGNORECASE), "verbosity", "detailed")
    ]

    @classmethod
    def extract_facts_and_preferences(
        cls,
        query: str,
        existing_facts: List[ConversationFact],
        existing_preferences: Dict[str, str]
    ) -> Tuple[List[ConversationFact], Dict[str, str]]:
        facts = list(existing_facts)
        preferences = dict(existing_preferences)
        q_lower = query.lower().strip()

        # 1. User Preference Update ("Keep answers short", "Explain in detail")
        for pat, key, val in cls.PREFERENCE_PATTERNS:
            if pat.search(q_lower):
                preferences[key] = val
                facts.append(ConversationFact(
                    content=f"User preference set: {key}={val}",
                    fact_type=FactType.PREFERENCE_FACT,
                    fact_status=FactStatus.USER_STATED
                ))

        # 2. User-Stated Deadline / Constraint Update ("Deadline is Friday", "Actually deadline changed to Monday")
        m = cls.DEADLINE_PATTERN.search(q_lower)
        if m:
            new_deadline = m.group(2).capitalize()
            # Mark previous deadline facts as EXPIRED / CONFLICTING
            for f in facts:
                if f.fact_type == FactType.CONSTRAINT_FACT and "deadline" in f.content.lower():
                    f.fact_status = FactStatus.EXPIRED

            facts.append(ConversationFact(
                content=f"Deadline set to {new_deadline}",
                fact_type=FactType.CONSTRAINT_FACT,
                fact_status=FactStatus.USER_STATED,
                created_at=time.time()
            ))

        return facts, preferences
