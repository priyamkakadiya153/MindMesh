import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from .providers.pgvector.repository import PGVectorRepository

logger = logging.getLogger(__name__)

class VectorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider = PGVectorRepository(db)

    async def insert(self, chunk_id: UUID, embedding: list[float], model_name: str = "text-embedding-3-small") -> bool:
        """Inserts a single vector representation into active store."""
        return await self.provider.insert(chunk_id, embedding, model_name)

    async def insert_batch(self, batch_data: list[dict], model_name: str = "text-embedding-3-small") -> int:
        """Inserts batch of vector representations into active store."""
        return await self.provider.insert_batch(batch_data, model_name)

    async def update(self, chunk_id: UUID, embedding: list[float], model_name: str = "text-embedding-3-small") -> bool:
        """Updates a vector representation in active store."""
        return await self.provider.update(chunk_id, embedding, model_name)

    async def delete(self, chunk_id: UUID) -> bool:
        """Deletes a vector representation from active store."""
        return await self.provider.delete(chunk_id)

    async def search(self, query_vector: list[float], limit: int = 5, metric: str = "COSINE", filters: dict = None) -> list[dict]:
        """Searches vector store for nearest similarities."""
        return await self.provider.search(query_vector, limit, metric, filters)

    async def search_batch(self, query_vectors: list[list[float]], limit: int = 5, metric: str = "COSINE", filters: dict = None) -> list[list[dict]]:
        """Searches vector store for batch queries nearest similarities."""
        return await self.provider.search_batch(query_vectors, limit, metric, filters)

    async def get_statistics(self) -> dict:
        """Retrieves provider specific performance metrics and stats."""
        return await self.provider.get_statistics()
