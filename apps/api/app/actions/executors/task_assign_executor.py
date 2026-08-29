import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.task import Task
from .base import BaseActionExecutor
from ..types import ActionProposal, ActionResult, ActionResultStatus, ActionIntentType

logger = logging.getLogger(__name__)

class AssignTaskActionExecutor(BaseActionExecutor):
    """Assigns an existing workspace task to a workspace member."""

    async def execute(
        self,
        proposal: ActionProposal,
        user: User,
        db: AsyncSession
    ) -> ActionResult:
        try:
            workspace_id = user.current_workspace_id
            org_id = user.organization_id

            if not workspace_id:
                return ActionResult(
                    status=ActionResultStatus.NOT_AUTHORIZED,
                    action_type=ActionIntentType.ASSIGN_TASK,
                    message="No active workspace found.",
                    error_code="NO_ACTIVE_WORKSPACE"
                )

            params = proposal.parameters or {}
            task_name = params.get("task_name") or params.get("title") or ""
            assignee_name = params.get("assignee_name") or ""

            # 1. Resolve Assignee User
            user_stmt = select(User).where(
                User.organization_id == org_id,
                User.name.ilike(f"%{assignee_name}%")
            )
            user_res = await db.execute(user_stmt)
            matching_users = user_res.scalars().all()

            if not matching_users:
                return ActionResult(
                    status=ActionResultStatus.FAILED,
                    action_type=ActionIntentType.ASSIGN_TASK,
                    message=f"I couldn't find a workspace member named '{assignee_name}'.",
                    error_code="MEMBER_NOT_FOUND"
                )

            assignee_user = matching_users[0]

            # 2. Resolve Task
            task_stmt = select(Task).where(
                Task.workspace_id == workspace_id,
                Task.title.ilike(f"%{task_name}%")
            ).limit(5)
            task_res = await db.execute(task_stmt)
            tasks = task_res.scalars().all()

            if not tasks:
                return ActionResult(
                    status=ActionResultStatus.FAILED,
                    action_type=ActionIntentType.ASSIGN_TASK,
                    message=f"I couldn't find any task matching '{task_name}' in your workspace.",
                    error_code="ENTITY_NOT_FOUND"
                )

            target_task = tasks[0]
            target_task.assignee_id = assignee_user.id

            await db.commit()
            await db.refresh(target_task)

            msg = f"Done — Task '{target_task.title}' is now assigned to {assignee_user.name} ({assignee_user.email})."

            return ActionResult(
                status=ActionResultStatus.SUCCESS,
                action_type=ActionIntentType.ASSIGN_TASK,
                entity_type="TASK",
                entity_id=str(target_task.id),
                entity_name=target_task.title,
                message=msg,
                metadata={"task_id": str(target_task.id), "assignee_id": str(assignee_user.id)}
            )

        except Exception as e:
            logger.error(f"Failed assigning task: {str(e)}", exc_info=True)
            await db.rollback()
            return ActionResult(
                status=ActionResultStatus.FAILED,
                action_type=ActionIntentType.ASSIGN_TASK,
                message="I couldn't assign the task due to a backend error.",
                error_code="EXECUTION_FAILED"
            )
