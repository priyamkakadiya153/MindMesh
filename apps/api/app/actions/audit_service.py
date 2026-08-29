import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc

from app.models.user import User
from app.actions.audit_model import ActionEvent
from app.actions.types import ActionProposal, ActionResult, ActionResultStatus

logger = logging.getLogger(__name__)

class AuditService:
    """Service for immutably recording action audit events and querying action memory."""

    @classmethod
    async def record_action_event(
        cls,
        proposal: ActionProposal,
        result: ActionResult,
        user: User,
        db: AsyncSession,
        source_type: str = "AI_CHAT",
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None
    ) -> Optional[ActionEvent]:
        """Immutably logs an ActionEvent in PostgreSQL."""
        try:
            params = proposal.parameters or {}
            intent_str = proposal.intent_type.value if hasattr(proposal.intent_type, "value") else str(proposal.intent_type)
            event = ActionEvent(
                organization_id=user.organization_id,
                workspace_id=user.current_workspace_id,
                actor_user_id=user.id,
                action_type=intent_str,
                status=str(result.status.value if hasattr(result.status, "value") else result.status),
                source_type=params.get("source_type", source_type),
                target_type=result.entity_type or "ENTITY",
                target_id=result.entity_id or params.get("target_id"),
                before_state=before_state,
                after_state=after_state or result.metadata,
                conversation_id=proposal.parameters.get("conversation_id"),
                message_id=proposal.parameters.get("message_id"),
                reason=proposal.description or proposal.title
            )

            db.add(event)
            await db.commit()
            return event
        except Exception as e:
            logger.error(f"Failed to record action audit event: {str(e)}", exc_info=True)
            await db.rollback()
            return None

    @classmethod
    async def get_user_action_history(
        cls,
        user: User,
        db: AsyncSession,
        days: int = 7,
        source_type: Optional[str] = None,
        action_type: Optional[str] = None,
        limit: int = 50
    ) -> List[ActionEvent]:
        """Queries structured action history for current user & organization."""
        try:
            since = datetime.now(timezone.utc) - timedelta(days=days)
            stmt = select(ActionEvent).where(
                ActionEvent.organization_id == user.organization_id,
                ActionEvent.created_at >= since
            ).order_by(desc(ActionEvent.created_at)).limit(limit)

            if user.current_workspace_id:
                stmt = stmt.where(ActionEvent.workspace_id == user.current_workspace_id)
            if source_type:
                stmt = stmt.where(ActionEvent.source_type == source_type)
            if action_type:
                stmt = stmt.where(ActionEvent.action_type == action_type)

            res = await db.execute(stmt)
            return res.scalars().all()
        except Exception as e:
            logger.error(f"Failed fetching user action history: {str(e)}", exc_info=True)
            return []
