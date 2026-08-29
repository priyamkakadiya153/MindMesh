import logging
from uuid import UUID
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db_session
from app.api.dependencies import get_current_user
from app.authorization.organization_resolver import resolve_organization_id
from app.models.user import User
from app.models.document import Document
from app.ai.embeddings.models import DocumentChunk
from .models import Citation
from .generator import CitationValidator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Citation Rendering & Source Attribution"])

# ---------------- PYDANTIC SCHEMAS ----------------

class CitationResponse(BaseModel):
    id: UUID
    message_id: UUID
    conversation_id: Optional[UUID] = None
    document_id: UUID
    chunk_id: UUID
    document_title: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    similarity_score: float
    confidence_score: str
    citation_order: int
    citation_tag: str
    chunk_snippet: Optional[str] = None

class ChunkPreviewResponse(BaseModel):
    document_id: UUID
    chunk_id: UUID
    document_title: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    text: str
    character_count: int

class ValidateCitationsRequest(BaseModel):
    workspace_id: UUID
    citation_ids: List[UUID]

# ---------------- ENDPOINTS ----------------

@router.get("/chat/messages/{message_id}/citations", response_model=List[CitationResponse], status_code=status.HTTP_200_OK)
async def get_message_citations_endpoint(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves verifiable citation sources for a specific AI chat message."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id

    stmt = select(Citation).where(
        Citation.message_id == message_id,
        Citation.organization_id == org_uuid
    ).order_by(Citation.citation_order.asc())

    citations = (await db.execute(stmt)).scalars().all()
    results = []

    for cit in citations:
        # Join document title
        doc_stmt = select(Document.title, Document.name).where(Document.id == cit.document_id)
        doc_res = (await db.execute(doc_stmt)).first()
        doc_title = (doc_res.title or doc_res.name) if doc_res else "Untitled Document"

        # Join chunk snippet
        chunk_stmt = select(DocumentChunk.content).where(DocumentChunk.id == cit.chunk_id)
        chunk_res = (await db.execute(chunk_stmt)).scalar_one_or_none()
        snippet = chunk_res[:150] + "..." if chunk_res and len(chunk_res) > 150 else chunk_res

        results.append(CitationResponse(
            id=cit.id,
            message_id=cit.message_id,
            conversation_id=cit.conversation_id,
            document_id=cit.document_id,
            chunk_id=cit.chunk_id,
            document_title=doc_title,
            page_number=cit.page_number,
            section_title=cit.section_title,
            similarity_score=cit.similarity_score,
            confidence_score=cit.confidence_score,
            citation_order=cit.citation_order,
            citation_tag=cit.citation_tag,
            chunk_snippet=snippet
        ))

    return results

@router.get("/documents/{document_id}/chunks/{chunk_id}", response_model=ChunkPreviewResponse, status_code=status.HTTP_200_OK)
async def get_document_chunk_preview_endpoint(
    document_id: UUID,
    chunk_id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Fetches full chunk text and metadata for interactive document preview highlighting."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id

    doc_stmt = select(Document).where(
        Document.id == document_id,
        Document.organization_id == org_uuid,
        Document.deleted_at.is_(None)
    )
    doc = (await db.execute(doc_stmt)).scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized.")

    chunk_stmt = select(DocumentChunk).where(
        DocumentChunk.id == chunk_id,
        DocumentChunk.document_id == document_id,
        DocumentChunk.deleted_at.is_(None)
    )
    chunk = (await db.execute(chunk_stmt)).scalar_one_or_none()

    if not chunk:
        raise HTTPException(status_code=404, detail="Document chunk not found.")

    return ChunkPreviewResponse(
        document_id=document_id,
        chunk_id=chunk_id,
        document_title=doc.title or doc.name,
        page_number=chunk.page_number,
        section_title=chunk.section_title,
        text=chunk.content,
        character_count=chunk.character_count or len(chunk.content)
    )

@router.post("/chat/citations/validate", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def validate_citations_endpoint(
    request: ValidateCitationsRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Validates citations against organization and workspace boundaries."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id

    stmt = select(Citation).where(
        Citation.id.in_(request.citation_ids),
        Citation.organization_id == org_uuid,
        Citation.workspace_id == request.workspace_id
    )
    cits = (await db.execute(stmt)).scalars().all()

    valid_cits = await CitationValidator.validate_citations(db, list(cits), org_uuid, request.workspace_id)
    valid_ids = [str(c.id) for c in valid_cits]

    return {
        "total_requested": len(request.citation_ids),
        "valid_count": len(valid_ids),
        "valid_ids": valid_ids
    }
