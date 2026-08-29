import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.ai.answer.models import CitationItem

logger = logging.getLogger(__name__)

class AnswerValidator:
    """Post-generation validator for claims, citations, action outcomes, and groundings."""

    @classmethod
    def validate(
        cls,
        content: str,
        citations: List[CitationItem],
        evidence_items: List[Dict[str, Any]],
        reasoning_result: Optional[Dict[str, Any]] = None,
        action_results: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[bool, Optional[str]]:
        # 1. Action Consistency Check
        if action_results:
            failed_acts = [a for a in action_results if a.get("status") in ["FAILED", "WAITING_CONFIRMATION"]]
            if failed_acts:
                if re.search(r"\b(done|created successfully|completed successfully)\b", content, re.IGNORECASE):
                    return False, "Answer claims successful action completion despite action failure or block."

        # 2. Citation Verification
        valid_source_ids = set()
        for item in evidence_items:
            sid = item.get("source_id") or item.get("id")
            if sid:
                valid_source_ids.add(str(sid))

        for cit in citations:
            if cit.source_id not in valid_source_ids:
                return False, f"Citation '{cit.label}' references unknown/unverified source_id '{cit.source_id}'."

        # 3. Grounding & Fault Check
        if reasoning_result and reasoning_result.get("answer_readiness") == "INSUFFICIENT_EVIDENCE":
            c_lower = content.lower()
            if not any(k in c_lower for k in ["couldn't find", "could not find", "insufficient", "no information"]):
                return False, "Answer generates unsupported factual claim despite INSUFFICIENT_EVIDENCE status."

        return True, None
