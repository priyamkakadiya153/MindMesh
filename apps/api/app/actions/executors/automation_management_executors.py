import logging
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.automation.scheduled_automation_model import ScheduledAutomation
from app.automation.schedule_calculator import ScheduleCalculator
from app.automation.automation_resolver import AutomationResolver
from .base import BaseActionExecutor
from ..types import ActionProposal, ActionResult, ActionResultStatus, ActionIntentType

logger = logging.getLogger(__name__)

class PauseAutomationActionExecutor(BaseActionExecutor):
    """Executes PAUSE operation on a ScheduledAutomation record."""

    async def execute(
        self,
        proposal: ActionProposal,
        user: User,
        db: AsyncSession
    ) -> ActionResult:
        try:
            params = proposal.parameters or {}
            target_ref = params.get("target_ref") or params.get("name") or ""
            auto_id = params.get("automation_id")

            auto = None
            if auto_id:
                stmt = select(ScheduledAutomation).where(ScheduledAutomation.id == UUID(auto_id), ScheduledAutomation.user_id == user.id)
                res = await db.execute(stmt)
                auto = res.scalars().first()

            if not auto:
                auto, err_msg = await AutomationResolver.resolve(target_ref, user.id, db)
                if not auto:
                    return ActionResult(status=ActionResultStatus.FAILED, action_type=ActionIntentType.PAUSE_AUTOMATION, message=err_msg or "Automation not found.")

            auto.status = "PAUSED"
            await db.commit()

            msg = f"Done — automation '{auto.name}' has been paused. Future executions will stop until resumed."
            return ActionResult(
                status=ActionResultStatus.SUCCESS,
                action_type=ActionIntentType.PAUSE_AUTOMATION,
                entity_type="SCHEDULED_AUTOMATION",
                entity_id=str(auto.id),
                entity_name=auto.name,
                message=msg
            )
        except Exception as e:
            logger.error(f"Failed pausing automation: {str(e)}", exc_info=True)
            await db.rollback()
            return ActionResult(status=ActionResultStatus.FAILED, action_type=ActionIntentType.PAUSE_AUTOMATION, message="Failed pausing automation.")


class ResumeAutomationActionExecutor(BaseActionExecutor):
    """Executes RESUME operation on a ScheduledAutomation record."""

    async def execute(
        self,
        proposal: ActionProposal,
        user: User,
        db: AsyncSession
    ) -> ActionResult:
        try:
            params = proposal.parameters or {}
            target_ref = params.get("target_ref") or params.get("name") or ""
            auto_id = params.get("automation_id")

            auto = None
            if auto_id:
                stmt = select(ScheduledAutomation).where(ScheduledAutomation.id == UUID(auto_id), ScheduledAutomation.user_id == user.id)
                res = await db.execute(stmt)
                auto = res.scalars().first()

            if not auto:
                auto, err_msg = await AutomationResolver.resolve(target_ref, user.id, db)
                if not auto:
                    return ActionResult(status=ActionResultStatus.FAILED, action_type=ActionIntentType.RESUME_AUTOMATION, message=err_msg or "Automation not found.")

            auto.status = "ACTIVE"
            auto.next_run_at = ScheduleCalculator.calculate_next_run(
                schedule_type=auto.schedule_type,
                recurrence_rule=auto.recurrence_rule,
                tz_name=auto.timezone,
                from_utc=datetime.now(timezone.utc)
            )
            await db.commit()

            nxt_str = auto.next_run_at.strftime("%B %d, %Y at %I:%M %p") if auto.next_run_at else "Pending"
            msg = f"Done — automation '{auto.name}' has been resumed! Next run scheduled for {nxt_str}."
            return ActionResult(
                status=ActionResultStatus.SUCCESS,
                action_type=ActionIntentType.RESUME_AUTOMATION,
                entity_type="SCHEDULED_AUTOMATION",
                entity_id=str(auto.id),
                entity_name=auto.name,
                message=msg
            )
        except Exception as e:
            logger.error(f"Failed resuming automation: {str(e)}", exc_info=True)
            await db.rollback()
            return ActionResult(status=ActionResultStatus.FAILED, action_type=ActionIntentType.RESUME_AUTOMATION, message="Failed resuming automation.")


class CancelAutomationActionExecutor(BaseActionExecutor):
    """Executes CANCEL operation on a ScheduledAutomation record."""

    async def execute(
        self,
        proposal: ActionProposal,
        user: User,
        db: AsyncSession
    ) -> ActionResult:
        try:
            params = proposal.parameters or {}
            target_ref = params.get("target_ref") or params.get("name") or ""
            auto_id = params.get("automation_id")

            auto = None
            if auto_id:
                stmt = select(ScheduledAutomation).where(ScheduledAutomation.id == UUID(auto_id), ScheduledAutomation.user_id == user.id)
                res = await db.execute(stmt)
                auto = res.scalars().first()

            if not auto:
                auto, err_msg = await AutomationResolver.resolve(target_ref, user.id, db)
                if not auto:
                    return ActionResult(status=ActionResultStatus.FAILED, action_type=ActionIntentType.CANCEL_AUTOMATION, message=err_msg or "Automation not found.")

            auto.status = "CANCELLED"
            auto.next_run_at = None
            await db.commit()

            msg = f"Done — automation '{auto.name}' has been cancelled. Execution history remains available for audit."
            return ActionResult(
                status=ActionResultStatus.SUCCESS,
                action_type=ActionIntentType.CANCEL_AUTOMATION,
                entity_type="SCHEDULED_AUTOMATION",
                entity_id=str(auto.id),
                entity_name=auto.name,
                message=msg
            )
        except Exception as e:
            logger.error(f"Failed cancelling automation: {str(e)}", exc_info=True)
            await db.rollback()
            return ActionResult(status=ActionResultStatus.FAILED, action_type=ActionIntentType.CANCEL_AUTOMATION, message="Failed cancelling automation.")


class UpdateAutomationActionExecutor(BaseActionExecutor):
    """Executes UPDATE operation on a ScheduledAutomation record."""

    async def execute(
        self,
        proposal: ActionProposal,
        user: User,
        db: AsyncSession
    ) -> ActionResult:
        try:
            params = proposal.parameters or {}
            target_ref = params.get("target_ref") or params.get("name") or ""
            raw_q = (params.get("raw_query") or "").lower()
            auto_id = params.get("automation_id")

            auto = None
            if auto_id:
                stmt = select(ScheduledAutomation).where(ScheduledAutomation.id == UUID(auto_id), ScheduledAutomation.user_id == user.id)
                res = await db.execute(stmt)
                auto = res.scalars().first()

            if not auto:
                auto, err_msg = await AutomationResolver.resolve(target_ref, user.id, db)
                if not auto:
                    return ActionResult(status=ActionResultStatus.FAILED, action_type=ActionIntentType.UPDATE_AUTOMATION, message=err_msg or "Automation not found.")

            # Extract new schedule parameter details from raw_query if needed
            day_of_week = params.get("day_of_week")
            time_str = params.get("time_str")
            schedule_type = params.get("schedule_type")

            if not day_of_week and raw_q:
                import re
                for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                    if day in raw_q:
                        day_of_week = day.title()
                        schedule_type = "WEEKLY"
                        break

            if not time_str and raw_q:
                import re
                m = re.search(r'\bat\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', raw_q)
                if m:
                    time_str = m.group(1).upper()

            if schedule_type:
                auto.schedule_type = schedule_type
            if day_of_week:
                auto.recurrence_rule = f"every_{day_of_week.lower()}"

            # Update payload attributes
            payload = dict(auto.action_payload or {})
            if params.get("new_message_body"):
                payload["message_body"] = params["new_message_body"]
            if params.get("new_recipient_name"):
                payload["recipient_name"] = params["new_recipient_name"]
            if params.get("new_task_title"):
                payload["title"] = params["new_task_title"]
            if params.get("new_reminder_text"):
                payload["reminder_text"] = params["new_reminder_text"]

            auto.action_payload = payload

            # Recalculate next run
            auto.next_run_at = ScheduleCalculator.calculate_next_run(
                schedule_type=auto.schedule_type,
                time_str=time_str,
                day_of_week=day_of_week,
                tz_name=auto.timezone,
                from_utc=datetime.now(timezone.utc)
            )
            await db.commit()

            nxt_str = auto.next_run_at.strftime("%B %d, %Y at %I:%M %p") if auto.next_run_at else "Pending"
            msg = f"Done — automation '{auto.name}' updated! Next run scheduled for {nxt_str}."
            return ActionResult(
                status=ActionResultStatus.SUCCESS,
                action_type=ActionIntentType.UPDATE_AUTOMATION,
                entity_type="SCHEDULED_AUTOMATION",
                entity_id=str(auto.id),
                entity_name=auto.name,
                message=msg
            )
        except Exception as e:
            logger.error(f"Failed updating automation: {str(e)}", exc_info=True)
            await db.rollback()
            return ActionResult(status=ActionResultStatus.FAILED, action_type=ActionIntentType.UPDATE_AUTOMATION, message="Failed updating automation.")
