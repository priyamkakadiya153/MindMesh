import logging
from typing import Dict, Any, Optional
from app.ai.answer.models import AnswerType, AnswerRequest

logger = logging.getLogger(__name__)

class AnswerPlanner:
    """Plans answer structure, detail level, and source panel visibility."""

    @classmethod
    def plan_answer(cls, request: AnswerRequest) -> AnswerType:
        if request.action_results and len(request.action_results) > 0:
            return AnswerType.ACTION_RESULT

        readiness = "READY"
        if request.reasoning_result:
            readiness = request.reasoning_result.get("answer_readiness", "READY")

        if readiness == "INSUFFICIENT_EVIDENCE":
            return AnswerType.NO_RESULT

        if readiness == "CONFLICTING_EVIDENCE":
            return AnswerType.CONFLICT

        if readiness == "NEEDS_CLARIFICATION":
            return AnswerType.CLARIFICATION

        q_lower = request.original_query.lower()

        if any(k in q_lower for k in ["compare", "vs", "versus"]):
            return AnswerType.COMPARISON

        if any(k in q_lower for k in ["summarize", "summary", "overview"]):
            return AnswerType.SUMMARY

        if any(k in q_lower for k in ["why", "how", "explain"]):
            return AnswerType.EXPLANATION

        return AnswerType.DIRECT
