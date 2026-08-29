import logging
from uuid import UUID
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.actions.audit_model import ActionEvent

logger = logging.getLogger(__name__)

class CognitiveAgentAuditService:
    """
    CA-09 — Cognitive Agent Audit & Complete Traceability Service.
    Immutably records agent lifecycle, execution, memory, and candidate events in AUTO-07 ActionEvent audit log.
    """

    @staticmethod
    async def record_agent_event(
        db: AsyncSession,
        user: Any,
        organization_id: UUID,
        workspace_id: Optional[UUID],
        event_type: str,
        agent_id: UUID,
        target_id: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None
    ) -> Optional[ActionEvent]:
        """
        Records a Cognitive Agent event in AUTO-07 ActionEvent table.
        Safely handles detached or expired user ORM instances.
        """
        try:
            actor_id = None
            if user:
                actor_id = getattr(user, 'id', user)
                if isinstance(actor_id, str):
                    actor_id = UUID(actor_id)

            event = ActionEvent(
                organization_id=organization_id,
                workspace_id=workspace_id,
                actor_user_id=actor_id,
                action_type=f"COGNITIVE_AGENT_{event_type.upper()}",
                status="SUCCESS" if "FAILED" not in event_type.upper() else "FAILED",
                source_type="COGNITIVE_AGENT",
                target_type="COGNITIVE_AGENT",
                target_id=target_id or str(agent_id),
                before_state=before_state,
                after_state=after_state,
                reason=reason or f"Cognitive Agent event {event_type} for agent {agent_id}"
            )
            db.add(event)
            await db.commit()
            await db.refresh(event)
            return event
        except Exception as exc:
            logger.error(f"[CognitiveAudit] Failed to record audit event for agent {agent_id}: {exc}")
            try:
                await db.rollback()
            except Exception:
                pass
            return None
