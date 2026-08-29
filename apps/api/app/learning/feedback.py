import logging
from uuid import UUID
from typing import Optional, Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory.models import AgentFeedback

logger = logging.getLogger(__name__)

class FeedbackProcessor:
    @staticmethod
    async def record_feedback(
        db: AsyncSession,
        user_id: UUID,
        organization_id: UUID,
        feedback_type: str,
        rating: int,
        execution_id: Optional[UUID] = None,
        comment: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> AgentFeedback:
        """Stores explicit/implicit feedback signal logs to the database."""
        feedback = AgentFeedback(
            execution_id=execution_id,
            user_id=user_id,
            organization_id=organization_id,
            feedback_type=feedback_type,
            rating=rating,
            comment=comment,
            context_data=context_data,
            processed=False
        )
        db.add(feedback)
        await db.flush()
        logger.info(f"FeedbackProcessor: Logged rating {rating} feedback for user '{user_id}' on run '{execution_id}'")
        return feedback

    @staticmethod
    async def list_unprocessed_feedback(db: AsyncSession, organization_id: UUID) -> List[AgentFeedback]:
        stmt = select(AgentFeedback).where(
            AgentFeedback.organization_id == organization_id,
            AgentFeedback.processed == False
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
