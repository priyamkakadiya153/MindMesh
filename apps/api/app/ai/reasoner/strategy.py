import re
from typing import Dict, Any, Optional
from app.ai.reasoner.models import ReasoningMode

class ReasoningStrategySelector:
    """Selects the appropriate reasoning strategy for a request."""

    @classmethod
    def select_strategy(
        cls,
        query: str,
        intent_info: Optional[Dict[str, Any]] = None,
        action_results: Optional[list] = None
    ) -> ReasoningMode:
        if action_results and len(action_results) > 0:
            return ReasoningMode.ACTION_RESULT

        q_lower = query.lower().strip()

        # Calculation keywords
        if any(k in q_lower for k in ["percentage", "how many", "total", "count", "%", "ratio", "sum"]):
            return ReasoningMode.CALCULATION

        # Temporal keywords
        if any(k in q_lower for k in ["since", "before", "last week", "history", "previous owner", "changed"]):
            return ReasoningMode.TEMPORAL

        # Causal keywords
        if any(k in q_lower for k in ["why", "reason for", "cause of", "because"]):
            return ReasoningMode.CAUSAL

        # Comparison keywords
        if any(k in q_lower for k in ["compare", "versus", "vs", "which is better", "further ahead"]):
            return ReasoningMode.COMPARISON

        # Intent-driven overrides
        if intent_info:
            intent_type = str(intent_info.get("primary_intent", "")).upper()
            if "SUMMARY" in intent_type or "OVERVIEW" in intent_type:
                return ReasoningMode.SYNTHESIS

        # Default fallback
        if len(query.split()) > 8:
            return ReasoningMode.SYNTHESIS

        return ReasoningMode.DIRECT
