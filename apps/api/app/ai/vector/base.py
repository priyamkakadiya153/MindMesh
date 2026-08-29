from abc import ABC, abstractmethod
from uuid import UUID

class BaseVectorStore(ABC):
    @abstractmethod
    async def insert(self, chunk_id: UUID, embedding: list[float], metadata: dict) -> bool:
        """Inserts vector representation into store index."""
        pass

    @abstractmethod
    async def delete(self, chunk_id: UUID) -> bool:
        """Removes a vector representation from index."""
        pass

    @abstractmethod
    async def search(self, embedding: list[float], limit: int = 5, filters: dict = None) -> list[dict]:
        """Searches index returns similarities matches list."""
        pass
