import logging
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.reasoner.models import (
    ReasoningRequest,
    ReasoningResult,
    AnswerContext,
    ReasoningStatus,
    AnswerReadiness
)
from app.ai.reasoner.orchestrator import ContextOrchestrator
from .intent import QueryIntentDetector
from .sanitizer import PromptInjectionSanitizer
from .evidence import EvidenceRanker
from .citations import CitationValidator
from .suggestions import FollowUpGenerator

from ..rag.retrieval import RAGRetrieval
from ..rag.evaluation import RAGEvaluator
from app.timeline.temporal_retriever import TimelineRetriever
from app.knowledge.graph_retriever import GraphRetriever
from app.models.user import User as UserModel
from ..llm.factory import LLMProviderFactory, LLMSettings, UnifiedLLMResponse

logger = logging.getLogger(__name__)

class MindMeshReasoner:
    """Master Organizational Knowledge Reasoning Engine."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.retrieval = RAGRetrieval(db)
        self.tl_retriever = TimelineRetriever(db)
        self.graph_retriever = GraphRetriever(db)

    async def analyze(self, user_id: UUID, org_id: UUID, query: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Provides a reasoning plan summary for orchestrator logging."""
        intent_info = QueryIntentDetector.detect(query)
        return {
            "intent": intent_info.get("intent", "KNOWLEDGE_QUERY"),
            "steps": ["Detect Intent", "Retrieve Knowledge", "Evaluate Evidence", "Synthesize Answer"],
            "requires_retrieval": intent_info.get("requires_retrieval", True)
        }

    @classmethod
    def orchestrate_reasoning(cls, req: ReasoningRequest) -> Tuple[ReasoningResult, AnswerContext]:
        """Synchronous Reasoning Orchestration facade for AI-08 pipeline integration."""
        result = ContextOrchestrator.orchestrate(req)

        citations = []
        if result.supporting_evidence:
            for item in result.supporting_evidence:
                citations.append({
                    "id": item.get("source_id", "doc"),
                    "type": item.get("source_type", "DOCUMENT"),
                    "title": item.get("title", "Evidence Source")
                })

        answer_ctx = AnswerContext(
            question=req.original_query,
            conclusion=result.conclusion,
            evidence=result.supporting_evidence,
            citations=citations,
            uncertainties=result.uncertainties,
            conflicts=result.conflicting_evidence,
            entities=result.resolved_entities,
            action_results=result.action_effects,
            answer_readiness=result.answer_readiness
        )

        return result, answer_ctx

    async def reason_and_answer(
        self,
        user_id: UUID,
        organization_id: UUID,
        query: str,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        provider: str = "gemini",
        model: str = "gemini-2.5-flash",
        temperature: float = 0.2,
        max_tokens: int = 1024,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:

        intent_info = QueryIntentDetector.detect(query)
        user_obj = UserModel(id=user_id)

        retrieved_chunks = await self.retrieval.retrieve_grounded_chunks(
            user_id=user_id,
            org_id=organization_id,
            query=query,
            workspace_id=workspace_id,
            project_id=project_id,
            limit=10
        )

        timeline_events = await self.tl_retriever.get_temporal_context(
            user=user_obj,
            organization_id=organization_id,
            query_text=query,
            workspace_id=workspace_id,
            top_k=10
        )

        graph_context = await self.graph_retriever.expand_context(
            user=user_obj,
            organization_id=organization_id,
            query_text=query,
            workspace_id=workspace_id,
            top_nodes=5
        )

        evidence = EvidenceRanker.assemble_and_rank(
            retrieved_chunks=retrieved_chunks,
            timeline_events=timeline_events,
            graph_context=graph_context,
            intent_info=intent_info
        )

        # AI-08 Orchestration
        req = ReasoningRequest(
            request_id=UUID(int=0),
            original_query=query,
            user_id=user_id,
            workspace_id=workspace_id or UUID(int=0),
            organization_id=organization_id,
            supporting_evidence=evidence
        )

        result, answer_ctx = self.orchestrate_reasoning(req)
        clean_query = PromptInjectionSanitizer.sanitize(query)

        prompt = f"""
You are MindMesh AI Knowledge Assistant. Answer the user query strictly based on the provided evidence.

Query: {clean_query}

Evidence:
{answer_ctx.evidence}

Reasoning Status: {result.status.value}
Uncertainties: {result.uncertainties}
Conflicts: {result.conflicting_evidence}

Answer concisely, accurately, and neutrally. Attach citations where evidence exists.
"""

        provider_inst = LLMProviderFactory.get_provider(provider, model)
        from app.ai.gateway.models import AIRequest
        ai_req = AIRequest(
            user_id=user_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            message=prompt,
            generation_parameters={"temperature": temperature, "max_tokens": max_tokens}
        )

        llm_resp = await provider_inst.generate_response(ai_req)
        raw_answer = llm_resp.content

        validated_citations = CitationValidator.validate(answer_ctx.citations, raw_answer)
        suggestions = FollowUpGenerator.generate(query, raw_answer)

        return {
            "query": query,
            "answer": raw_answer,
            "citations": validated_citations,
            "confidence": 0.95 if result.status == ReasoningStatus.COMPLETE else 0.40,
            "readiness": result.answer_readiness.value,
            "uncertainties": result.uncertainties,
            "conflicts": result.conflicting_evidence,
            "suggestions": suggestions,
            "tokens": {
                "prompt": llm_resp.usage.prompt_tokens if llm_resp.usage else 0,
                "completion": llm_resp.usage.completion_tokens if llm_resp.usage else 0,
            },
            "latency_ms": llm_resp.timing.total_latency_ms if llm_resp.timing else 0
        }
