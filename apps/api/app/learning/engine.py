import logging
from uuid import UUID
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.learning.feedback import FeedbackProcessor
from app.learning.adaptation import AdaptationLayer
from app.memory.consolidation import MemoryConsolidator

logger = logging.getLogger(__name__)

class LearningEngine:
    @staticmethod
    async def learn(
        db: AsyncSession,
        user_id: UUID,
        organization_id: UUID,
        rating: int,
        execution_id: Optional[UUID] = None,
        comment: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Saves a user feedback record for continuous learning ingestion."""
        feedback = await FeedbackProcessor.record_feedback(
            db=db,
            user_id=user_id,
            organization_id=organization_id,
            feedback_type="explicit_rating",
            rating=rating,
            execution_id=execution_id,
            comment=comment,
            context_data=context_data
        )
        return feedback

    @staticmethod
    async def consolidate(
        db: AsyncSession,
        organization_id: UUID,
        scope_key: str,
        memory_type: str,
        key: str
    ) -> Any:
        """Consolidates separate records of a given type/key into a single long-term memory."""
        return await MemoryConsolidator.consolidate_session_memories(
            db=db,
            organization_id=organization_id,
            scope_key=scope_key,
            memory_type=memory_type,
            key=key
        )

    @staticmethod
    async def retrieve_adapted_context(
        db: AsyncSession,
        organization_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Loads customized prompt parameters adapted based on positive user reviews."""
        return await AdaptationLayer.get_adaptation_overrides(
            db=db,
            organization_id=organization_id,
            user_id=user_id
        )
