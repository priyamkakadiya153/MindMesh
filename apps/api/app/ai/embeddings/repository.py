from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from .models import DocumentChunk, DocumentEmbedding

class EmbeddingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def clear_document_chunks(self, document_id: UUID) -> None:
        """Deletes all chunks linked to the selected document ID."""
        stmt = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        await self.db.execute(stmt)
        await self.db.flush()

    async def get_document_chunks(self, document_id: UUID) -> list[DocumentChunk]:
        stmt = select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def save_chunk(self, document_id: UUID, index: int, text: str, token_count: int, metadata: dict) -> DocumentChunk:
        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=index,
            content=text,
            token_count=token_count,
            metadata_json=metadata
        )
        self.db.add(chunk)
        await self.db.flush()
        return chunk
