import re
import logging
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_

from app.models.user import User
from app.models.task import Task
from app.notifications.time_parser import NaturalTimeParser
from .base import BaseActionExecutor
from ..types import ActionProposal, ActionResult, ActionResultStatus, ActionIntentType

logger = logging.getLogger(__name__)

class CreateTaskActionExecutor(BaseActionExecutor):
    """Executes REAL database mutations to insert a Task into PostgreSQL for AUTO-02."""

    @classmethod
    def extract_clean_task_title(cls, raw_title: str) -> str:
        """Extracts clean action subject, stripping query wrapper phrases."""
        if not raw_title or not raw_title.strip():
            return "New Workspace Task"

        clean = raw_title.strip()
        # Strip prefixes like "Create a task to...", "Add a task to...", "Create task..."
        prefix_pattern = r"^(?:create\s+(?:a\s+)?task\s+(?:to\s+)?|add\s+(?:a\s+)?task\s+(?:to\s+)?|create\s+a\s+todo\s+(?:to\s+)?|put\s+this\s+on\s+my\s+task\s+list\s+to\s+)"
        clean = re.sub(prefix_pattern, "", clean, flags=re.IGNORECASE).strip()

        # Strip trailing date phrases like "... tomorrow", "... by Friday" if present
        clean = re.sub(r"\s+(?:by|before|until|due|on|for)?\s*(?:tomorrow|friday|monday|tuesday|wednesday|thursday|saturday|sunday|eod|next week)\b", "", clean, flags=re.IGNORECASE).strip()

        return clean.capitalize() if clean else raw_title.capitalize()

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
                    action_type=ActionIntentType.CREATE_TASK,
                    message="No active workspace found for user to create task.",
                    error_code="NO_ACTIVE_WORKSPACE"
                )

            params = proposal.parameters or {}
            raw_title = params.get("title") or params.get("raw_query") or "New Workspace Task"
            clean_title = self.extract_clean_task_title(raw_title)

            description = params.get("description") or f"Created via AI Action Execution for {user.email}"
            assignee_name = params.get("assignee_name")
            due_date_str = params.get("due_date_str") or params.get("due_date")
            allow_duplicate = params.get("allow_duplicate", False)

            # 1. Duplicate Task Protection Check
            if not allow_duplicate:
                dup_stmt = select(Task).where(
                    Task.workspace_id == workspace_id,
                    Task.title.ilike(clean_title),
                    Task.status.in_(["TODO", "OPEN", "IN_PROGRESS"]),
                    Task.deleted_at.is_(None)
                )
                dup_res = await db.execute(dup_stmt)
                existing_task = dup_res.scalar_one_or_none()
                if existing_task:
                    logger.info(f"Duplicate task detected for title '{clean_title}' in workspace {workspace_id}")
                    return ActionResult(
                        status=ActionResultStatus.SUCCESS,
                        action_type=ActionIntentType.CREATE_TASK,
                        entity_type="TASK",
                        entity_id=str(existing_task.id),
                        entity_name=existing_task.title,
                        message=f"You already have an active task called '{existing_task.title}'.",
                        metadata={
                            "task_id": str(existing_task.id),
                            "is_duplicate": True,
                            "existing_task_id": str(existing_task.id),
                            "workspace_id": str(workspace_id)
                        }
                    )

            # 2. Due Date Resolution
            due_datetime = None
            if due_date_str:
                if isinstance(due_date_str, datetime):
                    due_datetime = due_date_str
                else:
                    try:
                        parsed_dt, _ = NaturalTimeParser.parse_time(str(due_date_str))
                        due_datetime = parsed_dt.replace(tzinfo=None)
                    except Exception:
                        due_datetime = None

            # 3. Assignee User Resolution
            assignee_id = None
            if assignee_name:
                user_stmt = select(User).where(
                    or_(
                        User.first_name.ilike(f"%{assignee_name}%"),
                        User.last_name.ilike(f"%{assignee_name}%"),
                        User.username.ilike(f"%{assignee_name}%")
                    )
                )
                user_res = await db.execute(user_stmt)
                matching_users = user_res.scalars().all()
                if len(matching_users) == 1:
                    assignee_id = matching_users[0].id
                elif len(matching_users) > 1:
                    logger.info(f"Multiple workspace users matched '{assignee_name}'. Left unassigned for safety.")

            # 4. Provenance Fields
            source_type = params.get("source_type", "CONVERSATION")
            conv_id = UUID(params["conversation_id"]) if params.get("conversation_id") and isinstance(params["conversation_id"], str) and len(params["conversation_id"]) == 36 else None
            msg_id = UUID(params["message_id"]) if params.get("message_id") and isinstance(params["message_id"], str) and len(params["message_id"]) == 36 else None

            # 5. Insert Task Record into PostgreSQL
            new_task = Task(
                id=uuid4(),
                title=clean_title,
                description=description,
                status="TODO",
                task_type="TASK",
                priority="MEDIUM",
                due_date=due_datetime,
                organization_id=org_id,
                workspace_id=workspace_id,
                assignee_id=assignee_id,
                source_type=source_type,
                conversation_id=conv_id,
                message_id=msg_id,
                is_ai_extracted=True,
                created_at=datetime.utcnow()
            )

            db.add(new_task)
            await db.commit()
            await db.refresh(new_task)

            # 6. Post-Execution Persistence Verification
            verif_stmt = select(Task).where(Task.id == new_task.id)
            verif_res = await db.execute(verif_stmt)
            persisted = verif_res.scalar_one_or_none()
            if not persisted:
                return ActionResult(
                    status=ActionResultStatus.FAILED,
                    action_type=ActionIntentType.CREATE_TASK,
                    message="I couldn't create the task because database persistence failed. Nothing was changed.",
                    error_code="PERSISTENCE_VERIFICATION_FAILED"
                )

            assignee_text = f" and assigned to {assignee_name}" if assignee_id else ""
            due_text = f" for {due_date_str}" if due_date_str else ""
            msg = f"Done — I created the task '{clean_title}'{due_text}{assignee_text}."

            logger.info(f"[AUTO-02 REAL MUTATION SUCCESS] Created task '{clean_title}' (ID: {new_task.id}) for user {user.email} in workspace {workspace_id}")

            return ActionResult(
                status=ActionResultStatus.SUCCESS,
                action_type=ActionIntentType.CREATE_TASK,
                entity_type="TASK",
                entity_id=str(new_task.id),
                entity_name=clean_title,
                message=msg,
                metadata={
                    "task_id": str(new_task.id),
                    "title": clean_title,
                    "status": "TODO",
                    "due_date": due_datetime.isoformat() if due_datetime else None,
                    "due_date_str": due_date_str,
                    "assignee_name": assignee_name,
                    "workspace_id": str(workspace_id),
                    "source_type": source_type
                }
            )

        except Exception as e:
            logger.error(f"Failed to execute task creation mutation: {str(e)}", exc_info=True)
            await db.rollback()
            return ActionResult(
                status=ActionResultStatus.FAILED,
                action_type=ActionIntentType.CREATE_TASK,
                message="I couldn't create the task due to a backend database error. Nothing was changed.",
                error_code="EXECUTION_FAILED"
            )
