import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from .models import DocumentChunk, DocumentEmbedding

logger = logging.getLogger(__name__)

async def get_embedding_status(db: AsyncSession, document_id: UUID) -> dict:
    """Retrieves embedding generation status statistics for a document."""
    # Count chunks
    stmt_chunks = select(func.count(DocumentChunk.id)).where(DocumentChunk.document_id == document_id)
    chunks_count = (await db.execute(stmt_chunks)).scalar() or 0
    
    # Count generated embeddings
    stmt_emb = select(func.count(DocumentEmbedding.id)).join(
        DocumentChunk, DocumentChunk.id == DocumentEmbedding.chunk_id
    ).where(DocumentChunk.document_id == document_id)
    embeddings_count = (await db.execute(stmt_emb)).scalar() or 0
    
    # Determine overall status
    if chunks_count == 0:
        status = "NOT_STARTED"
    elif embeddings_count < chunks_count:
        status = "PARTIAL"
    else:
        status = "COMPLETED"
        
    return {
        "document_id": str(document_id),
        "status": status,
        "chunks_count": chunks_count,
        "embeddings_count": embeddings_count
    }
