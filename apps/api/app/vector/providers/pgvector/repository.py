import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ....ai.embeddings.models import DocumentEmbedding
from .search import search_pgvector
from .statistics import get_pgvector_stats

logger = logging.getLogger(__name__)

class PGVectorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def insert(self, chunk_id: UUID, embedding: list[float], model_name: str = "text-embedding-3-small") -> bool:
        """Inserts or updates a single embedding in the database."""
        stmt = select(DocumentEmbedding).where(DocumentEmbedding.chunk_id == chunk_id)
        res = await self.db.execute(stmt)
        record = res.scalar_one_or_none()
        
        if record:
            record.embedding = embedding
            record.embedding_dimension = len(embedding)
            record.embedding_model = model_name
        else:
            record = DocumentEmbedding(
                chunk_id=chunk_id,
                embedding_model=model_name,
                embedding_dimension=len(embedding),
                embedding=embedding,
                checksum="checksum_abc"
            )
            self.db.add(record)
        await self.db.flush()
        return True

    async def insert_batch(self, batch_data: list[dict], model_name: str = "text-embedding-3-small") -> int:
        """Inserts a batch of embeddings in the database."""
        count = 0
        for item in batch_data:
            chunk_id = item["chunk_id"]
            embedding = item["embedding"]
            success = await self.insert(chunk_id, embedding, model_name)
            if success:
                count += 1
        return count

    async def update(self, chunk_id: UUID, embedding: list[float], model_name: str = "text-embedding-3-small") -> bool:
        """Updates a vector embedding."""
        return await self.insert(chunk_id, embedding, model_name)

    async def delete(self, chunk_id: UUID) -> bool:
        """Deletes a vector embedding by chunk id."""
        stmt = delete(DocumentEmbedding).where(DocumentEmbedding.chunk_id == chunk_id)
        await self.db.execute(stmt)
        await self.db.flush()
        return True

    async def search(self, query_vector: list[float], limit: int = 5, metric: str = "COSINE", filters: dict = None) -> list[dict]:
        """Performs similarity search against the stored vector embeddings."""
        return await search_pgvector(self.db, query_vector, limit, metric, filters)

    async def search_batch(self, query_vectors: list[list[float]], limit: int = 5, metric: str = "COSINE", filters: dict = None) -> list[list[dict]]:
        """Performs batch similarity search against the stored vector embeddings."""
        results = []
        for qv in query_vectors:
            res = await self.search(qv, limit, metric, filters)
            results.append(res)
        return results

    async def get_statistics(self) -> dict:
        """Retrieves pgvector operational statistics."""
        return await get_pgvector_stats(self.db)
