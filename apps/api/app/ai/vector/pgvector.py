import math
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from .base import BaseVectorStore
from ..embeddings.models import DocumentEmbedding, DocumentChunk

class PGVectorStore(BaseVectorStore):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def insert(self, chunk_id: UUID, embedding: list[float], metadata: dict) -> bool:
        # Check if exists
        stmt = select(DocumentEmbedding).where(DocumentEmbedding.chunk_id == chunk_id)
        res = await self.db.execute(stmt)
        record = res.scalar_one_or_none()
        
        if record:
            record.embedding = embedding
            record.embedding_dimension = len(embedding)
        else:
            record = DocumentEmbedding(
                chunk_id=chunk_id,
                embedding_model="text-embedding-3-small",
                embedding_dimension=len(embedding),
                embedding=embedding,
                checksum="checksum_abc"
            )
            self.db.add(record)
            
        await self.db.flush()
        return True

    async def delete(self, chunk_id: UUID) -> bool:
        stmt = delete(DocumentEmbedding).where(DocumentEmbedding.chunk_id == chunk_id)
        await self.db.execute(stmt)
        await self.db.flush()
        return True

    @staticmethod
    def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
        """Calculates cosine similarity between two float vectors list."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm_a = math.sqrt(sum(a * a for a in v1))
        norm_b = math.sqrt(sum(b * b for b in v2))
        
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
            
        return dot_product / (norm_a * norm_b)

    async def search(self, embedding: list[float], limit: int = 5, filters: dict = None) -> list[dict]:
        """Loads chunks embeddings list and filters in Python memory using cosine similarity."""
        stmt = select(DocumentEmbedding, DocumentChunk).join(
            DocumentChunk, DocumentChunk.id == DocumentEmbedding.chunk_id
        )
        res = await self.db.execute(stmt)
        rows = res.all()
        
        scored_matches = []
        for row in rows:
            emb_record, chunk_record = row
            
            # Apply organizational/project isolation filters
            if filters:
                meta = chunk_record.metadata_json
                match = True
                for k, v in filters.items():
                    if str(meta.get(k)) != str(v):
                        match = False
                        break
                if not match:
                    continue
                    
            similarity = self._cosine_similarity(embedding, emb_record.embedding)
            scored_matches.append({
                "chunk_id": chunk_record.id,
                "document_id": chunk_record.document_id,
                "content": chunk_record.content,
                "metadata": chunk_record.metadata_json,
                "similarity": similarity
            })
            
        scored_matches.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_matches[:limit]
