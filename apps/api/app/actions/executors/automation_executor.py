import logging
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.automation.scheduled_automation_model import ScheduledAutomation
from app.automation.schedule_calculator import ScheduleCalculator
from .base import BaseActionExecutor
from ..types import ActionProposal, ActionResult, ActionResultStatus, ActionIntentType

logger = logging.getLogger(__name__)

class CreateAutomationActionExecutor(BaseActionExecutor):
    """Executes creation of a real ScheduledAutomation record in PostgreSQL."""

    async def execute(
        self,
        proposal: ActionProposal,
        user: User,
        db: AsyncSession
    ) -> ActionResult:
        try:
            org_id = user.organization_id
            workspace_id = user.current_workspace_id

            params = proposal.parameters or {}
            mgmt_action = params.get("management_action")
            if mgmt_action == "PAUSE":
                from .automation_management_executors import PauseAutomationActionExecutor
                return await PauseAutomationActionExecutor().execute(proposal, user, db)
            elif mgmt_action == "RESUME":
                from .automation_management_executors import ResumeAutomationActionExecutor
                return await ResumeAutomationActionExecutor().execute(proposal, user, db)
            elif mgmt_action == "CANCEL":
                from .automation_management_executors import CancelAutomationActionExecutor
                return await CancelAutomationActionExecutor().execute(proposal, user, db)
            elif mgmt_action == "UPDATE":
                from .automation_management_executors import UpdateAutomationActionExecutor
                return await UpdateAutomationActionExecutor().execute(proposal, user, db)

            name = params.get("name") or proposal.title or "Scheduled Automation"
            action_type = params.get("action_type") or "CREATE_REMINDER"
            action_payload = params.get("action_payload") or {}
            schedule_type = params.get("schedule_type") or "DAILY"
            time_str = params.get("time_str")
            day_of_week = params.get("day_of_week")
            user_tz = user.timezone or "Asia/Kolkata"

            # Parse start_datetime or calculated next_run_at
            from_utc = None
            if params.get("start_datetime_utc"):
                try:
                    from_utc = datetime.fromisoformat(params["start_datetime_utc"])
                except Exception:
                    pass

            next_run = ScheduleCalculator.calculate_next_run(
                schedule_type=schedule_type,
                time_str=time_str,
                day_of_week=day_of_week,
                tz_name=user_tz,
                from_utc=from_utc
            )

            source_conv = getattr(proposal, "source_conversation_id", None) or params.get("source_conversation_id") or params.get("conversation_id")
            automation = ScheduledAutomation(
                id=uuid4(),
                user_id=user.id,
                organization_id=org_id,
                workspace_id=workspace_id,
                name=name,
                action_type=action_type,
                action_payload=action_payload,
                schedule_type=schedule_type,
                recurrence_rule=params.get("recurrence_rule"),
                timezone=user_tz,
                start_at=datetime.now(timezone.utc),
                next_run_at=next_run,
                status="ACTIVE",
                source_conversation_id=source_conv
            )
            db.add(automation)
            await db.commit()
            await db.refresh(automation)

            # Post-Execution DB Persistence Verification
            from sqlalchemy import select
            verif_stmt = select(ScheduledAutomation).where(ScheduledAutomation.id == automation.id)
            verif_res = await db.execute(verif_stmt)
            persisted = verif_res.scalar_one_or_none()
            if not persisted:
                return ActionResult(
                    status=ActionResultStatus.FAILED,
                    action_type=ActionIntentType.CREATE_AUTOMATION,
                    message="I couldn't create the automation because database persistence failed. Nothing was created.",
                    error_code="PERSISTENCE_VERIFICATION_FAILED"
                )

            next_str = next_run.strftime("%B %d, %Y at %I:%M %p") if next_run else "Pending"
            msg = f"Done — automation '{name}' has been created! Next execution scheduled for {next_str} ({user_tz})."
            logger.info(f"[AUTO-04 AUTOMATION CREATED] ID: {automation.id}, Name: {name}, Next Run: {next_str}")

            return ActionResult(
                status=ActionResultStatus.SUCCESS,
                action_type=ActionIntentType.CREATE_AUTOMATION,
                entity_type="SCHEDULED_AUTOMATION",
                entity_id=str(automation.id),
                entity_name=name,
                message=msg,
                metadata={
                    "automation_id": str(automation.id),
                    "name": name,
                    "schedule_type": schedule_type,
                    "next_run_at": next_str,
                    "timezone": user_tz
                }
            )

        except Exception as e:
            logger.error(f"Failed creating scheduled automation: {str(e)}", exc_info=True)
            await db.rollback()
            return ActionResult(
                status=ActionResultStatus.FAILED,
                action_type=ActionIntentType.CREATE_AUTOMATION,
                message="I couldn't create the automation due to a backend error. Nothing was created.",
                error_code="EXECUTION_FAILED"
            )
