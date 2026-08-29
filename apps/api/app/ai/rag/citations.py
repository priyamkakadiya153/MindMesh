import logging
from uuid import UUID
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from ..citations.engine import CitationEngine
from ..citations.models import Citation

logger = logging.getLogger(__name__)

class RAGCitations:
    @staticmethod
    async def extract_citations(
        db: AsyncSession,
        user_id: UUID,
        org_id: UUID,
        answer_text: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> List[Citation]:
        """Aligns citations inline and compiles details."""
        return await CitationEngine.generate_citations(
            db=db,
            user_id=user_id,
            org_id=org_id,
            ai_response=answer_text,
            retrieved_chunks=retrieved_chunks
        )
