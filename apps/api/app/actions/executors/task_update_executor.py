import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.task import Task
from .base import BaseActionExecutor
from ..types import ActionProposal, ActionResult, ActionResultStatus, ActionIntentType

logger = logging.getLogger(__name__)

class UpdateTaskActionExecutor(BaseActionExecutor):
    """Updates task properties (title, deadline, priority, project) in PostgreSQL."""

    async def execute(
        self,
        proposal: ActionProposal,
        user: User,
        db: AsyncSession
    ) -> ActionResult:
        try:
            workspace_id = user.current_workspace_id
            if not workspace_id:
                return ActionResult(
                    status=ActionResultStatus.NOT_AUTHORIZED,
                    action_type=ActionIntentType.UPDATE_TASK,
                    message="No active workspace found.",
                    error_code="NO_ACTIVE_WORKSPACE"
                )

            params = proposal.parameters or {}
            task_name = params.get("task_name") or params.get("title") or ""

            # Find matching task in workspace
            stmt = select(Task).where(
                Task.workspace_id == workspace_id,
                Task.title.ilike(f"%{task_name}%")
            ).limit(5)
            res = await db.execute(stmt)
            tasks = res.scalars().all()

            if not tasks:
                return ActionResult(
                    status=ActionResultStatus.FAILED,
                    action_type=ActionIntentType.UPDATE_TASK,
                    message=f"I couldn't find any task matching '{task_name}' in your workspace.",
                    error_code="ENTITY_NOT_FOUND"
                )

            target_task = tasks[0]

            # Apply updates
            updates_applied = []
            if params.get("new_title"):
                target_task.title = params["new_title"]
                updates_applied.append(f"renamed to '{params['new_title']}'")
            if params.get("new_deadline_str"):
                updates_applied.append(f"deadline set to {params['new_deadline_str']}")
            if params.get("priority"):
                target_task.priority = params["priority"].upper()
                updates_applied.append(f"priority set to {params['priority']}")

            await db.commit()
            await db.refresh(target_task)

            update_text = ", ".join(updates_applied) if updates_applied else "updated"
            msg = f"Done — Task '{target_task.title}' was successfully {update_text}."

            return ActionResult(
                status=ActionResultStatus.SUCCESS,
                action_type=ActionIntentType.UPDATE_TASK,
                entity_type="TASK",
                entity_id=str(target_task.id),
                entity_name=target_task.title,
                message=msg,
                metadata={"task_id": str(target_task.id)}
            )

        except Exception as e:
            logger.error(f"Failed updating task: {str(e)}", exc_info=True)
            await db.rollback()
            return ActionResult(
                status=ActionResultStatus.FAILED,
                action_type=ActionIntentType.UPDATE_TASK,
                message="I couldn't update the task due to a backend error.",
                error_code="EXECUTION_FAILED"
            )
