from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.retrieval.models import RetrievalRequest, RetrievalPlan, EvidenceItem, SourceType
from app.ai.retrieval.adapters.base import BaseRetrievalAdapter
from app.ai.retrieval.retriever import HybridRetriever

class DocumentSearchAdapter(BaseRetrievalAdapter):
    """Retrieves document chunks using Hybrid Vector & Keyword search."""

    async def search(self, request: RetrievalRequest, plan: RetrievalPlan) -> List[EvidenceItem]:
        results: List[EvidenceItem] = []
        if SourceType.DOCUMENT not in plan.sources:
            return results

        hr = HybridRetriever(self.db)
        query_text = plan.queries[0] if plan.queries else request.original_query

        search_res = await hr.hybrid_search(
            query_text=query_text,
            organization_id=request.organization_id,
            workspace_id=request.workspace_id,
            top_k=plan.max_results or 10
        )

        chunks = search_res.get("chunks", [])
        for c in chunks:
            match_type = c.get("match_type", "hybrid")
            methods = ["semantic", "keyword"] if match_type == "hybrid" else [match_type]

            results.append(EvidenceItem(
                source_id=str(c.get("chunk_id")),
                source_type=SourceType.DOCUMENT,
                title=c.get("title") or "Untitled Document",
                content=c.get("content") or "",
                score=float(c.get("score", 0.70)),
                authority_score=0.85,
                recency_score=0.75,
                location={
                    "document_id": str(c.get("document_id")),
                    "chunk_id": str(c.get("chunk_id")),
                    "section_title": c.get("section_title"),
                    "page_number": c.get("page_number")
                },
                metadata={"file_type": c.get("file_type")},
                retrieval_methods=methods
            ))

        return results
