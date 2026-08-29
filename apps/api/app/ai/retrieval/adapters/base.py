from abc import ABC, abstractmethod
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.retrieval.models import RetrievalRequest, RetrievalPlan, EvidenceItem

class BaseRetrievalAdapter(ABC):
    """Abstract interface for all domain retrieval adapters."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @abstractmethod
    async def search(self, request: RetrievalRequest, plan: RetrievalPlan) -> List[EvidenceItem]:
        """Executes targeted search and returns normalized EvidenceItem records."""
        pass

    async def health_check(self) -> bool:
        """Returns True if the underlying storage engine is available."""
        return True
