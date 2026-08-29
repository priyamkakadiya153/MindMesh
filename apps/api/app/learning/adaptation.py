import logging
from uuid import UUID
from typing import Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory.models import AgentFeedback

logger = logging.getLogger(__name__)

class AdaptationLayer:
    @staticmethod
    async def get_adaptation_overrides(db: AsyncSession, organization_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Calculates prompt overrides based on historical high-rating feedback patterns."""
        stmt = select(AgentFeedback).where(
            AgentFeedback.organization_id == organization_id,
            AgentFeedback.user_id == user_id,
            AgentFeedback.rating >= 4
        )
        res = await db.execute(stmt)
        positive_logs = res.scalars().all()

        overrides = {
            "style": "neutral",
            "verbosity": "standard",
            "preferred_format": None
        }

        # Analyze comments/context for common patterns
        styles = [log.context_data.get("style") for log in positive_logs if log.context_data and "style" in log.context_data]
        if styles:
            overrides["style"] = max(set(styles), key=styles.count)

        formats = [log.context_data.get("format") for log in positive_logs if log.context_data and "format" in log.context_data]
        if formats:
            overrides["preferred_format"] = max(set(formats), key=formats.count)

        return overrides
