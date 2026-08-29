import time
import asyncio
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.retrieval.models import (
    RetrievalRequest,
    RetrievalPlan,
    EvidenceItem,
    EvidenceSet,
    EvidenceCoverage,
    SourceType
)
from app.ai.retrieval.planner import RetrievalPlanner
from app.ai.retrieval.reranker import RetrievalReranker
from app.ai.retrieval.adapters.structured import StructuredDataSearchAdapter
from app.ai.retrieval.adapters.document import DocumentSearchAdapter
from app.ai.retrieval.adapters.conversation import ConversationSearchAdapter
from app.ai.retrieval.domain_retriever import MultiDomainRetriever

logger = logging.getLogger(__name__)

class HybridRetrievalEngine:
    """
    MindMesh Hybrid Knowledge Retrieval Engine.
    
    Responsibilities:
    - Multi-tenant permission & security boundary verification
    - Retrieval planning based on AI-03 intent and AI-04 context
    - Parallel multi-source search (Structured DB, Document vector/keyword, Conversation history)
    - Deduplication & multi-criteria reranking
    - EvidenceSet packaging for downstream reasoning
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.structured_adapter = StructuredDataSearchAdapter(db)
        self.document_adapter = DocumentSearchAdapter(db)
        self.conversation_adapter = ConversationSearchAdapter(db)

    async def retrieve_knowledge(self, request: RetrievalRequest) -> EvidenceSet:
        start_time = time.time()

        # 1. Authorization & Security Boundary Check
        mdr = MultiDomainRetriever(self.db)
        has_access = await mdr.verify_user_access(
            user_id=request.user_id,
            organization_id=request.organization_id,
            workspace_id=request.workspace_id
        )
        if not has_access:
            logger.warning(f"[RetrievalEngine] Access denied for User {request.user_id} in Organization {request.organization_id}")
            return EvidenceSet(
                query=request.original_query,
                items=[],
                coverage=EvidenceCoverage.NONE,
                confidence="INSUFFICIENT",
                latency_ms=int((time.time() - start_time) * 1000),
                trace={"error": "PERMISSION_FILTERED"}
            )

        # 2. Retrieval Planning
        plan = RetrievalPlanner.plan(request)
        if not plan.sources:
            return EvidenceSet(
                query=request.original_query,
                items=[],
                coverage=EvidenceCoverage.NONE,
                confidence="STRONG",
                latency_ms=int((time.time() - start_time) * 1000),
                trace={"plan": "NO_RETRIEVAL_REQUIRED"}
            )

        # 3. Parallel Multi-Source Dispatch
        tasks = []
        sources_attempted = plan.sources
        sources_succeeded = []

        if SourceType.PROJECT in plan.sources or SourceType.TASK in plan.sources:
            tasks.append(self.structured_adapter.search(request, plan))
        if SourceType.DOCUMENT in plan.sources:
            tasks.append(self.document_adapter.search(request, plan))
        if SourceType.CONVERSATION in plan.sources or SourceType.MESSAGE in plan.sources:
            tasks.append(self.conversation_adapter.search(request, plan))

        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        candidates: List[EvidenceItem] = []
        for idx, res in enumerate(raw_results):
            if isinstance(res, Exception):
                logger.error(f"[RetrievalEngine] Retrieval adapter task {idx} failed: {str(res)}")
            elif isinstance(res, list):
                candidates.extend(res)
                sources_succeeded.extend([item.source_type for item in res])

        sources_succeeded = list(set(sources_succeeded))

        # 4. Extract Entity Mentions from Intent for Reranking
        intent_entities = []
        if request.intent_result and hasattr(request.intent_result, "entities"):
            intent_entities = [e.text for e in request.intent_result.entities]

        # 5. Deduplicate and Rerank
        final_items = RetrievalReranker.rerank(candidates, plan, intent_entities)

        # 6. Assess Evidence Coverage
        coverage = EvidenceCoverage.GOOD
        if not final_items:
            coverage = EvidenceCoverage.NONE
        elif len(final_items) < 3:
            coverage = EvidenceCoverage.PARTIAL

        confidence = "STRONG" if coverage == EvidenceCoverage.GOOD else ("MODERATE" if coverage == EvidenceCoverage.PARTIAL else "INSUFFICIENT")

        latency_ms = int((time.time() - start_time) * 1000)

        return EvidenceSet(
            query=request.original_query,
            items=final_items,
            coverage=coverage,
            confidence=confidence,
            latency_ms=latency_ms,
            sources_attempted=sources_attempted,
            sources_succeeded=sources_succeeded,
            trace={
                "plan_sources": [s.value for s in plan.sources],
                "candidates_found": len(candidates),
                "final_selected": len(final_items)
            }
        )
