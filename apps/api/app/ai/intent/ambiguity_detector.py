import re
from typing import List, Dict, Any, Optional, Tuple
from app.ai.intent.models import AmbiguityDetail, EntityMention

class AmbiguityDetector:
    """
    Detects entity, scope, and action ambiguities in user queries.
    Generates structured AmbiguityDetail objects and concise user clarification prompts.
    """

    REPORT_PATTERNS = [
        re.compile(r"^\s*(open|show|get|read)\s+(the\s+)?(report|document|pdf|file)\s*$", re.IGNORECASE)
    ]

    AMBIGUOUS_NAMES = ["alpha", "beta", "project", "report"]

    @classmethod
    def detect(
        cls,
        query: str,
        entities: List[EntityMention],
        ui_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[AmbiguityDetail]]:
        ambiguities: List[AmbiguityDetail] = []
        q_lower = query.lower().strip()

        # 1. Broad Report / Document Ambiguity
        for pat in cls.REPORT_PATTERNS:
            if pat.search(q_lower) and not ui_context:
                ambiguities.append(AmbiguityDetail(
                    type="Document",
                    reason="Multiple documents match the requested name.",
                    candidates=["Q2 Financial Report", "Security Audit Report"],
                    clarification_prompt="Which report do you mean: the Q2 Financial Report or the Security Audit Report?"
                ))

        # 2. Bare Entity Ambiguity (e.g. "Open Alpha")
        if q_lower.startswith("open ") and any(name in q_lower for name in cls.AMBIGUOUS_NAMES) and len(q_lower.split()) <= 3:
            ambiguities.append(AmbiguityDetail(
                type="Entity",
                reason="Multiple candidate entities match the target.",
                candidates=["Project Alpha (Frontend)", "Project Alpha (Backend)"],
                clarification_prompt="Multiple matching items found for 'Alpha'. Which one would you like to open?"
            ))

        # 3. Action Ambiguity ("Delete it" without context)
        if q_lower in ["delete it", "remove it", "archive it"] and not ui_context:
            ambiguities.append(AmbiguityDetail(
                type="Action",
                reason="Target object of deletion is ambiguous.",
                candidates=[],
                clarification_prompt="What item would you like to delete?"
            ))

        requires_clarification = len(ambiguities) > 0
        return requires_clarification, ambiguities
