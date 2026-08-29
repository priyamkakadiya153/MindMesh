import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.notifications.reminder_model import Reminder
from .base import BaseActionExecutor
from ..types import ActionProposal, ActionResult, ActionResultStatus, ActionIntentType

logger = logging.getLogger(__name__)

class CancelReminderActionExecutor(BaseActionExecutor):
    """Cancels a scheduled reminder by changing status to CANCELLED."""

    async def execute(
        self,
        proposal: ActionProposal,
        user: User,
        db: AsyncSession
    ) -> ActionResult:
        try:
            params = proposal.parameters or {}
            keyword = params.get("keyword") or params.get("reminder_text") or ""

            stmt = select(Reminder).where(
                Reminder.user_id == user.id,
                Reminder.status == "SCHEDULED",
                Reminder.title.ilike(f"%{keyword}%")
            ).limit(5)

            res = await db.execute(stmt)
            reminders = res.scalars().all()

            if not reminders:
                return ActionResult(
                    status=ActionResultStatus.FAILED,
                    action_type=ActionIntentType.CREATE_REMINDER,
                    message=f"I couldn't find any scheduled reminder matching '{keyword}'.",
                    error_code="ENTITY_NOT_FOUND"
                )

            target_rem = reminders[0]
            target_rem.status = "CANCELLED"

            await db.commit()
            await db.refresh(target_rem)

            msg = f"Done — The reminder '{target_rem.title}' has been cancelled."

            return ActionResult(
                status=ActionResultStatus.SUCCESS,
                action_type=ActionIntentType.CREATE_REMINDER,
                entity_type="REMINDER",
                entity_id=str(target_rem.id),
                entity_name=target_rem.title,
                message=msg,
                metadata={"reminder_id": str(target_rem.id), "status": "CANCELLED"}
            )

        except Exception as e:
            logger.error(f"Failed cancelling reminder: {str(e)}", exc_info=True)
            await db.rollback()
            return ActionResult(
                status=ActionResultStatus.FAILED,
                action_type=ActionIntentType.CREATE_REMINDER,
                message="I couldn't cancel the reminder due to a backend error.",
                error_code="EXECUTION_FAILED"
            )
