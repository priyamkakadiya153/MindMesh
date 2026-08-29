from typing import List, Dict, Any, Optional
from app.ai.retrieval.models import RetrievalRequest, RetrievalPlan, SourceType

class RetrievalPlanner:
    """
    Formulates a RetrievalPlan based on AI-03 Intent and AI-04 Conversation Context.
    Ensures targeted retrieval without searching unnecessary sources.
    """

    @classmethod
    def plan(cls, request: RetrievalRequest) -> RetrievalPlan:
        intent_val = getattr(request.intent_result, "intent", None)
        intent_str = intent_val.value if hasattr(intent_val, "value") else str(intent_val or "UNKNOWN")
        requires_retrieval = getattr(request.intent_result, "requires_retrieval", True)

        # 1. No Retrieval needed for Greetings or General Knowledge
        if not requires_retrieval or intent_str in {"GREETING", "THANKS", "GENERAL_KNOWLEDGE"}:
            return RetrievalPlan(
                sources=[],
                queries=[request.original_query],
                max_results=0,
                rerank_required=False
            )

        sources: List[SourceType] = []
        queries: List[str] = [request.normalized_query or request.original_query]

        # Add rewritten query from conversation context if present
        rewritten = getattr(request.intent_result, "rewritten_query", None)
        if rewritten and rewritten not in queries:
            queries.append(rewritten)

        # 2. Map Intent to Primary Sources
        if intent_str in {"PROJECT_QUERY", "STATUS_REQUEST"}:
            sources = [SourceType.PROJECT, SourceType.TASK]
        elif intent_str == "TASK_QUERY":
            sources = [SourceType.TASK, SourceType.PROJECT]
        elif intent_str == "DOCUMENT_QUERY":
            sources = [SourceType.DOCUMENT]
        elif intent_str in {"CONVERSATION_QUERY", "MEETING_QUERY"}:
            sources = [SourceType.CONVERSATION, SourceType.MESSAGE]
        elif intent_str == "DECISION_QUERY":
            sources = [SourceType.DECISION, SourceType.CONVERSATION, SourceType.DOCUMENT]
        elif intent_str in {"SEARCH_QUERY", "SUMMARY_REQUEST", "COMPARISON_REQUEST"}:
            sources = [SourceType.DOCUMENT, SourceType.PROJECT, SourceType.TASK, SourceType.CONVERSATION]
        else:
            sources = [SourceType.DOCUMENT, SourceType.PROJECT, SourceType.TASK, SourceType.CONVERSATION]

        # Include user or context source hints if provided
        if request.source_hints:
            for hint in request.source_hints:
                if hint not in sources:
                    sources.append(hint)

        return RetrievalPlan(
            sources=sources,
            queries=queries,
            filters=request.filters,
            time_range=request.time_range,
            max_results=request.max_results,
            rerank_required=True
        )
