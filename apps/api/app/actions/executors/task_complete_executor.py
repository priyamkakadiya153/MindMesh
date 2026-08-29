import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.task import Task
from .base import BaseActionExecutor
from ..types import ActionProposal, ActionResult, ActionResultStatus, ActionIntentType

logger = logging.getLogger(__name__)

class CompleteTaskActionExecutor(BaseActionExecutor):
    """Marks an existing task status as COMPLETED in PostgreSQL."""

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
                    action_type=ActionIntentType.COMPLETE_TASK,
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
                    action_type=ActionIntentType.COMPLETE_TASK,
                    message=f"I couldn't find any task matching '{task_name}' in your workspace.",
                    error_code="ENTITY_NOT_FOUND"
                )

            target_task = tasks[0]
            target_task.status = "COMPLETED"

            await db.commit()
            await db.refresh(target_task)

            msg = f"Done — Task '{target_task.title}' is now marked as completed."

            return ActionResult(
                status=ActionResultStatus.SUCCESS,
                action_type=ActionIntentType.COMPLETE_TASK,
                entity_type="TASK",
                entity_id=str(target_task.id),
                entity_name=target_task.title,
                message=msg,
                metadata={"task_id": str(target_task.id), "status": "COMPLETED"}
            )

        except Exception as e:
            logger.error(f"Failed completing task: {str(e)}", exc_info=True)
            await db.rollback()
            return ActionResult(
                status=ActionResultStatus.FAILED,
                action_type=ActionIntentType.COMPLETE_TASK,
                message="I couldn't mark the task as complete due to a backend error.",
                error_code="EXECUTION_FAILED"
            )
