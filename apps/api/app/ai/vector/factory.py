from sqlalchemy.ext.asyncio import AsyncSession
from .pgvector import PGVectorStore

class VectorStoreFactory:
    @staticmethod
    def get_vector_store(db: AsyncSession) -> PGVectorStore:
        """Resolves active vector store provider driver instance."""
        return PGVectorStore(db)
