import logging
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from .types import ActionIntentType, ActionProposal, ActionResult
from .executors.base import BaseActionExecutor
from .executors.task_executor import CreateTaskActionExecutor
from .executors.task_update_executor import UpdateTaskActionExecutor
from .executors.task_assign_executor import AssignTaskActionExecutor
from .executors.task_complete_executor import CompleteTaskActionExecutor
from .executors.reminder_create_executor import CreateReminderActionExecutor
from .executors.reminder_cancel_executor import CancelReminderActionExecutor
from .executors.direct_message_executor import DirectMessageActionExecutor
from .executors.automation_executor import CreateAutomationActionExecutor
from .executors.automation_management_executors import (
    PauseAutomationActionExecutor,
    ResumeAutomationActionExecutor,
    CancelAutomationActionExecutor,
    UpdateAutomationActionExecutor
)
from .executors.unimplemented import UnimplementedActionExecutor

from .policy import ActionSafetyPolicy
from .safety_guard import ActionSafetyGuard
from .types import ActionResultStatus

logger = logging.getLogger(__name__)

class ActionRegistry:
    """Central registry and dispatcher mapping ActionIntentTypes to ActionExecutors with Safety Controls."""

    def __init__(self):
        self._executors: Dict[ActionIntentType, BaseActionExecutor] = {
            ActionIntentType.CREATE_TASK: CreateTaskActionExecutor(),
            ActionIntentType.UPDATE_TASK: UpdateTaskActionExecutor(),
            ActionIntentType.ASSIGN_TASK: AssignTaskActionExecutor(),
            ActionIntentType.COMPLETE_TASK: CompleteTaskActionExecutor(),
            ActionIntentType.CREATE_REMINDER: CreateReminderActionExecutor(),
            ActionIntentType.SEND_DIRECT_MESSAGE: DirectMessageActionExecutor(),
            ActionIntentType.CREATE_AUTOMATION: CreateAutomationActionExecutor(),
            ActionIntentType.PAUSE_AUTOMATION: PauseAutomationActionExecutor(),
            ActionIntentType.RESUME_AUTOMATION: ResumeAutomationActionExecutor(),
            ActionIntentType.CANCEL_AUTOMATION: CancelAutomationActionExecutor(),
            ActionIntentType.UPDATE_AUTOMATION: UpdateAutomationActionExecutor(),
            ActionIntentType.CREATE_DECISION: UnimplementedActionExecutor(),
        }
        self._executed_proposals: Dict[str, ActionResult] = {}

    def get_executor(self, intent_type: ActionIntentType) -> BaseActionExecutor:
        return self._executors.get(intent_type, UnimplementedActionExecutor())

    async def dispatch(
        self,
        proposal: ActionProposal,
        user: User,
        db: AsyncSession
    ) -> ActionResult:
        # 1. Idempotency Check (Prevents duplicate execution on double-click or retry)
        if proposal.proposal_id in self._executed_proposals:
            logger.info(f"Duplicate submission blocked by Idempotency Guard for proposal_id: {proposal.proposal_id}")
            return self._executed_proposals[proposal.proposal_id]

        # 2. Centralized Safety Policy Check
        evaluation = ActionSafetyPolicy.evaluate(proposal.intent_type, proposal.parameters)
        if evaluation.is_blocked:
            return ActionResult(
                status=ActionResultStatus.FAILED,
                action_type=proposal.intent_type,
                message=evaluation.block_reason or "Action blocked by safety policy."
            )

        # 3. Proposal Expiration Check (15-minute TTL)
        is_valid_ttl, ttl_err = ActionSafetyGuard.validate_expiration(proposal, evaluation.expiration_minutes)
        if not is_valid_ttl:
            return ActionResult(
                status=ActionResultStatus.FAILED,
                action_type=proposal.intent_type,
                message=ttl_err or "Proposal expired."
            )

        # 4. Workspace Scope Validation
        is_valid_ws, ws_err = ActionSafetyGuard.validate_workspace_scope(proposal, user)
        if not is_valid_ws:
            return ActionResult(
                status=ActionResultStatus.FAILED,
                action_type=proposal.intent_type,
                message=ws_err or "Workspace validation failed."
            )

        # 5. Dispatch to Action Executor
        executor = self.get_executor(proposal.intent_type)
        raw_result = await executor.execute(proposal, user, db)

        # 6. Post-Execution State Verification
        verified_result = await ActionSafetyGuard.verify_post_execution(proposal, raw_result, user, db)

        # Cache result for Idempotency
        if verified_result.status == ActionResultStatus.SUCCESS:
            self._executed_proposals[proposal.proposal_id] = verified_result

        # 7. Immutably Record Audit Trail Event in PostgreSQL
        try:
            from .audit_service import AuditService
            await AuditService.record_action_event(
                proposal=proposal,
                result=verified_result,
                user=user,
                db=db,
                source_type=proposal.parameters.get("source_type", "AI_CHAT")
            )
        except Exception as e:
            logger.error(f"Failed logging audit event: {str(e)}", exc_info=True)

        return verified_result

action_registry = ActionRegistry()
