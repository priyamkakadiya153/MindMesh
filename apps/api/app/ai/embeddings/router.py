import logging
from uuid import UUID
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.api.dependencies import get_current_user
from app.authorization.organization_resolver import resolve_organization_id
from app.models.user import User
from .service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Embeddings & Vectorization"])

# ---------------- PYDANTIC SCHEMAS ----------------

class GenerateEmbeddingsRequest(BaseModel):
    provider: Optional[str] = Field("gemini", description="e.g. gemini, openai, ollama")
    model: Optional[str] = Field(None, description="e.g. text-embedding-004, text-embedding-3-small, nomic-embed-text")

class GenerateEmbeddingsResponse(BaseModel):
    document_id: UUID
    status: str
    message: str
    vectors_generated: int = 0
    provider: str = "gemini"
    model: str = "text-embedding-004"

class WorkspaceEmbeddingMetricsResponse(BaseModel):
    organization_id: UUID
    workspace_id: Optional[UUID] = None
    total_chunks: int = 0
    embedded_chunks: int = 0
    pending_chunks: int = 0
    completion_percentage: float = 100.0
    default_model: str = "text-embedding-004"

class DocumentEmbeddingStatusResponse(BaseModel):
    document_id: UUID
    status: str
    total_chunks: int = 0
    embedded_vectors: int = 0
    embedding_model: str = "text-embedding-004"
    dimension: int = 768
    version: int = 1
    generated_at: Optional[str] = None

# ---------------- ENDPOINTS ----------------

@router.get("/embeddings/status", response_model=WorkspaceEmbeddingMetricsResponse, status_code=status.HTTP_200_OK)
async def get_global_embedding_status(
    workspace_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Fetches global or workspace vector embedding status & chunk completion metrics."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    service = EmbeddingService(db)
    metrics = await service.get_workspace_embedding_metrics(org_uuid, workspace_id)
    return WorkspaceEmbeddingMetricsResponse(**metrics)

@router.post("/embeddings/regenerate", response_model=Dict[str, Any], status_code=status.HTTP_202_ACCEPTED)
async def regenerate_workspace_embeddings_endpoint(
    background_tasks: BackgroundTasks,
    workspace_id: Optional[UUID] = Query(None),
    provider: str = Query("gemini"),
    model: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Triggers background re-embedding for all document chunks in workspace."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    
    async def run_reembed():
        from app.core.database import AsyncSessionLocal
        from app.documents.models import Document
        from sqlalchemy import select
        async with AsyncSessionLocal() as session:
            stmt = select(Document).where(Document.organization_id == org_uuid, Document.deleted_at.is_(None))
            if workspace_id:
                stmt = stmt.where(Document.workspace_id == workspace_id)
            res = await session.execute(stmt)
            docs = res.scalars().all()
            svc = EmbeddingService(session)
            for d in docs:
                try:
                    await svc.generate_document_embeddings(d.id, provider, model)
                except Exception as e:
                    logger.error(f"Failed to re-embed doc {d.id}: {e}")

    background_tasks.add_task(run_reembed)

    return {
        "status": "QUEUED",
        "message": f"Workspace embedding regeneration queued using provider '{provider}'.",
        "workspace_id": str(workspace_id) if workspace_id else None
    }

@router.post("/documents/{document_id}/embeddings", response_model=GenerateEmbeddingsResponse, status_code=status.HTTP_200_OK)
async def generate_document_embeddings_endpoint(
    document_id: UUID,
    request: Optional[GenerateEmbeddingsRequest] = None,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Generates vector embeddings for a specific document's chunks."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    req_provider = request.provider if request else "gemini"
    req_model = request.model if request else None

    service = EmbeddingService(db)
    count = await service.generate_document_embeddings(
        document_id=document_id,
        provider_name=req_provider,
        model_name=req_model
    )

    return GenerateEmbeddingsResponse(
        document_id=document_id,
        status="COMPLETED",
        message=f"Successfully generated {count} vector embeddings.",
        vectors_generated=count,
        provider=req_provider,
        model=req_model or ("text-embedding-004" if "gemini" in req_provider else "text-embedding-3-small")
    )

@router.get("/documents/{document_id}/embeddings", response_model=DocumentEmbeddingStatusResponse, status_code=status.HTTP_200_OK)
async def get_document_embedding_status_endpoint(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Fetches vector embedding metadata status for a specific document."""
    service = EmbeddingService(db)
    status_dict = await service.get_document_embedding_status(document_id)
    if status_dict.get("generated_at"):
        status_dict["generated_at"] = status_dict["generated_at"].isoformat()

    return DocumentEmbeddingStatusResponse(**status_dict)
