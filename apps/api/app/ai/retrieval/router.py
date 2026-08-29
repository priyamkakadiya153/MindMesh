import logging
from uuid import UUID
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.api.dependencies import get_current_user
from app.authorization.organization_resolver import resolve_organization_id
from app.models.user import User
from .retriever import HybridRetriever

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/retrieval", tags=["Hybrid Retrieval Engine"])

# ---------------- PYDANTIC SCHEMAS ----------------

class HybridSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language prompt or search keywords")
    workspace_id: Optional[UUID] = Field(None, description="Workspace ID to scope retrieval")
    top_k: int = Field(10, ge=1, le=50, description="Number of top context chunks to return")
    provider: str = Field("gemini", description="Embedding provider model (e.g. gemini, openai, ollama)")
    file_type: Optional[str] = Field(None, description="Optional filter by file extension (e.g. pdf, txt, docx)")

class RetrievedChunkResponse(BaseModel):
    chunk_id: UUID
    document_id: UUID
    title: str
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    content: str
    token_count: int = 0
    score: float
    match_type: str = "hybrid"
    file_type: Optional[str] = None

class HybridSearchResponse(BaseModel):
    query: str
    workspace_id: Optional[UUID] = None
    latency_ms: int
    total_candidates_found: int
    chunks: List[RetrievedChunkResponse]

# ---------------- ENDPOINTS ----------------

@router.post("/search", response_model=HybridSearchResponse, status_code=status.HTTP_200_OK)
async def search_hybrid_knowledge(
    request: HybridSearchRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Executes hybrid vector + keyword search over organization & workspace document chunks."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id

    retriever = HybridRetriever(db)
    result = await retriever.hybrid_search(
        query_text=request.query,
        organization_id=org_uuid,
        workspace_id=request.workspace_id,
        top_k=request.top_k,
        provider_name=request.provider,
        file_type=request.file_type
    )

    return HybridSearchResponse(
        query=result["query"],
        workspace_id=result["workspace_id"],
        latency_ms=result["latency_ms"],
        total_candidates_found=result["total_candidates_found"],
        chunks=[RetrievedChunkResponse(**c) for c in result["chunks"]]
    )
