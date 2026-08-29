import re
import logging
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.user import User
from app.notifications.reminder_model import Reminder
from app.notifications.time_parser import NaturalTimeParser
from .base import BaseActionExecutor
from ..types import ActionProposal, ActionResult, ActionResultStatus, ActionIntentType

logger = logging.getLogger(__name__)

class CreateReminderActionExecutor(BaseActionExecutor):
    """Parses natural time and persists a SCHEDULED Reminder in PostgreSQL for AUTO-02."""

    @classmethod
    def clean_reminder_title(cls, raw_title: str) -> str:
        """Strips query wrapper phrases like 'Remind me tomorrow to...'"""
        if not raw_title or not raw_title.strip():
            return "Workspace Reminder"

        clean = raw_title.strip()
        prefix_pattern = r"^(?:remind\s+me\s+(?:tomorrow|on\s+friday|on\s+monday|next\s+week|in\s+\d+\s+hours?|at\s+\d+\s*(?:am|pm)?)?\s+(?:to\s+|about\s+)?|don't\s+let\s+me\s+forget\s+(?:to\s+|about\s+)?|remind\s+me\s+to\s+)"
        clean = re.sub(prefix_pattern, "", clean, flags=re.IGNORECASE).strip()
        return clean.capitalize() if clean else raw_title.capitalize()

    async def execute(
        self,
        proposal: ActionProposal,
        user: User,
        db: AsyncSession
    ) -> ActionResult:
        try:
            params = proposal.parameters or {}
            raw_text = params.get("reminder_text") or params.get("title") or params.get("raw_query") or "Check on workspace tasks"
            clean_text = self.clean_reminder_title(raw_text)

            time_str = params.get("time_str") or params.get("due_date_str") or params.get("scheduled_time") or "in 1 hour"
            user_tz = params.get("timezone") or getattr(user, "timezone", None) or "Asia/Kolkata"
            allow_duplicate = params.get("allow_duplicate", False)

            # 1. Parse Natural Time into UTC datetime
            scheduled_utc, formatted_local = NaturalTimeParser.parse_time(time_str)

            # 2. Duplicate Active Reminder Protection Check
            if not allow_duplicate:
                dup_stmt = select(Reminder).where(
                    Reminder.user_id == user.id,
                    Reminder.title.ilike(clean_text),
                    Reminder.status == "SCHEDULED"
                )
                dup_res = await db.execute(dup_stmt)
                existing_rem = dup_res.scalar_one_or_none()
                if existing_rem:
                    logger.info(f"Duplicate active reminder detected for title '{clean_text}' for user {user.id}")
                    return ActionResult(
                        status=ActionResultStatus.SUCCESS,
                        action_type=ActionIntentType.CREATE_REMINDER,
                        entity_type="REMINDER",
                        entity_id=str(existing_rem.id),
                        entity_name=existing_rem.title,
                        message=f"You already have a scheduled reminder called '{existing_rem.title}' for {formatted_local}.",
                        metadata={
                            "reminder_id": str(existing_rem.id),
                            "is_duplicate": True,
                            "existing_reminder_id": str(existing_rem.id)
                        }
                    )

            # 3. Resolve Provenance Conversation ID
            conv_uuid = None
            if params.get("conversation_id") and isinstance(params["conversation_id"], str) and len(params["conversation_id"]) == 36:
                conv_uuid = UUID(params["conversation_id"])

            # 4. Insert Reminder Record in PostgreSQL
            new_reminder = Reminder(
                id=uuid4(),
                user_id=user.id,
                organization_id=user.organization_id,
                workspace_id=user.current_workspace_id,
                title=clean_text,
                scheduled_at=scheduled_utc,
                timezone=user_tz,
                status="SCHEDULED",
                source_conversation_id=conv_uuid
            )

            db.add(new_reminder)
            await db.commit()
            await db.refresh(new_reminder)

            # 5. Post-Execution Persistence Verification
            verif_stmt = select(Reminder).where(Reminder.id == new_reminder.id)
            verif_res = await db.execute(verif_stmt)
            persisted = verif_res.scalar_one_or_none()
            if not persisted:
                return ActionResult(
                    status=ActionResultStatus.FAILED,
                    action_type=ActionIntentType.CREATE_REMINDER,
                    message="I couldn't schedule the reminder because database persistence failed. Nothing was changed.",
                    error_code="PERSISTENCE_VERIFICATION_FAILED"
                )

            msg = f"Done — I'll remind you to '{clean_text}' on {formatted_local} ({user_tz})."

            logger.info(f"[AUTO-02 REMINDER CREATED SUCCESS] Persistent reminder {new_reminder.id} scheduled for {scheduled_utc} ({user_tz})")

            return ActionResult(
                status=ActionResultStatus.SUCCESS,
                action_type=ActionIntentType.CREATE_REMINDER,
                entity_type="REMINDER",
                entity_id=str(new_reminder.id),
                entity_name=clean_text,
                message=msg,
                metadata={
                    "reminder_id": str(new_reminder.id),
                    "title": clean_text,
                    "scheduled_at": scheduled_utc.isoformat(),
                    "formatted_time": formatted_local,
                    "timezone": user_tz,
                    "status": "SCHEDULED"
                }
            )

        except Exception as e:
            logger.error(f"Failed creating reminder: {str(e)}", exc_info=True)
            await db.rollback()
            return ActionResult(
                status=ActionResultStatus.FAILED,
                action_type=ActionIntentType.CREATE_REMINDER,
                message="I couldn't schedule the reminder due to a backend error. Nothing was changed.",
                error_code="EXECUTION_FAILED"
            )
