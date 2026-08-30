import uuid
import logging
from typing import List, Dict, Any, Tuple, Optional

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import Document
from app.ai.embeddings.models import DocumentChunk
from .models import Citation

logger = logging.getLogger(__name__)

class CitationGenerator:
    """Generates structured citation records from retrieved RAG document chunks."""

    @staticmethod
    def generate_citations(
        message_id: UUID,
        conversation_id: Optional[UUID],
        organization_id: UUID,
        workspace_id: UUID,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Tuple[List[Citation], bool]:
        """Deduplicates chunks, categorizes confidence scores, and formats citation tags."""
        if not retrieved_chunks:
            return [], False

        seen_chunk_ids = set()
        unique_chunks = []
        for chunk in retrieved_chunks:
            c_id = chunk.get("chunk_id") or chunk.get("id")
            if c_id and c_id not in seen_chunk_ids:
                seen_chunk_ids.add(c_id)
                unique_chunks.append(chunk)

        if not unique_chunks:
            return [], False

        citations = []
        for idx, chunk in enumerate(unique_chunks, start=1):
            score = float(chunk.get("score", 0.0) or chunk.get("similarity_score", 0.0))

            if score >= 0.85:
                confidence = "High"
            elif score >= 0.70:
                confidence = "Medium"
            else:
                confidence = "Low"

            doc_id = chunk.get("document_id")
            chunk_id = chunk.get("chunk_id") or chunk.get("id")

            if not doc_id or not chunk_id:
                continue

            doc_uuid = UUID(str(doc_id)) if not isinstance(doc_id, UUID) else doc_id
            chunk_uuid = UUID(str(chunk_id)) if not isinstance(chunk_id, UUID) else chunk_id

            cit = Citation(
                id=uuid.uuid4(),
                message_id=message_id,
                conversation_id=conversation_id,
                document_id=doc_uuid,
                chunk_id=chunk_uuid,
                organization_id=organization_id,
                workspace_id=workspace_id,
                page_number=chunk.get("page_number"),
                section_title=chunk.get("section_title") or "General Section",
                similarity_score=round(score, 4),
                score=round(score, 4),
                confidence_score=confidence,
                citation_order=idx,
                citation_tag=f"[{idx}]"
            )
            citations.append(cit)

        return citations, len(citations) > 0

class CitationValidator:
    """Validates citations against organizational isolation, workspace boundaries, and document existence."""

    @staticmethod
    async def validate_citations(
        db: AsyncSession,
        citations: List[Citation],
        organization_id: UUID,
        workspace_id: UUID
    ) -> List[Citation]:
        """Filters out citations referring to deleted or unauthorized documents/chunks."""
        valid_citations = []
        for cit in citations:
            # Check document existence and boundary
            doc_stmt = select(Document).where(
                Document.id == cit.document_id,
                Document.organization_id == organization_id,
                Document.workspace_id == workspace_id,
                Document.deleted_at.is_(None)
            )
            doc_res = (await db.execute(doc_stmt)).scalar_one_or_none()

            if not doc_res:
                logger.warning(f"Citation rejected: Document {cit.document_id} invalid or unauthorized.")
                continue

            # Check chunk existence
            chunk_stmt = select(DocumentChunk).where(
                DocumentChunk.id == cit.chunk_id,
                DocumentChunk.deleted_at.is_(None)
            )
            chunk_res = (await db.execute(chunk_stmt)).scalar_one_or_none()

            if not chunk_res:
                logger.warning(f"Citation rejected: Chunk {cit.chunk_id} missing or deleted.")
                continue

            valid_citations.append(cit)

        return valid_citations
