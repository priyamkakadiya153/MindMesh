import logging
from typing import Optional, Tuple
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.task import Task
from app.automation.scheduled_automation_model import ScheduledAutomation
from app.actions.types import ActionProposal, ActionResult, ActionResultStatus, ActionIntentType

logger = logging.getLogger(__name__)

class ActionSafetyGuard:
    """Re-validates action constraints before execution and verifies post-execution state."""

    @classmethod
    def validate_expiration(cls, proposal: ActionProposal, ttl_minutes: int = 15) -> Tuple[bool, Optional[str]]:
        now = datetime.now(timezone.utc)
        created_at = proposal.created_at or now
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if now - created_at > timedelta(minutes=ttl_minutes):
            return False, f"This action proposal has expired after {ttl_minutes} minutes. Please request the action again."
        return True, None

    @classmethod
    def validate_workspace_scope(cls, proposal: ActionProposal, user: User) -> Tuple[bool, Optional[str]]:
        if proposal.workspace_id and str(user.current_workspace_id) != str(proposal.workspace_id):
            return False, "Workspace mismatch. The pending action belongs to a different workspace."
        return True, None

    @classmethod
    async def verify_post_execution(
        cls,
        proposal: ActionProposal,
        result: ActionResult,
        user: User,
        db: AsyncSession
    ) -> ActionResult:
        """Verifies that entity modification actually persisted in PostgreSQL."""

        if result.status != ActionResultStatus.SUCCESS:
            return result

        try:
            intent = proposal.intent_type
            params = proposal.parameters or {}

            # Verify Task creation/update
            if intent in [ActionIntentType.CREATE_TASK, ActionIntentType.UPDATE_TASK]:
                if result.entity_id:
                    stmt = select(Task).where(Task.id == UUID(result.entity_id))
                    res = await db.execute(stmt)
                    task = res.scalars().first()
                    if not task:
                        return ActionResult(
                            status=ActionResultStatus.FAILED,
                            action_type=intent,
                            message="Execution verification failed: Task record was not found in database."
                        )

            # Verify Scheduled Automation creation/management
            elif intent == ActionIntentType.CREATE_AUTOMATION:
                if result.entity_id:
                    stmt = select(ScheduledAutomation).where(ScheduledAutomation.id == UUID(result.entity_id))
                    res = await db.execute(stmt)
                    auto = res.scalars().first()
                    if not auto:
                        return ActionResult(
                            status=ActionResultStatus.FAILED,
                            action_type=intent,
                            message="Execution verification failed: Automation record was not found in database."
                        )
                    mgmt_action = params.get("management_action")
                    if mgmt_action == "PAUSE" and auto.status != "PAUSED":
                        return ActionResult(
                            status=ActionResultStatus.FAILED,
                            action_type=intent,
                            message="Execution verification failed: Automation status is not PAUSED."
                        )

            return result
        except Exception as e:
            logger.error(f"Post-execution verification error: {str(e)}", exc_info=True)
            return result
