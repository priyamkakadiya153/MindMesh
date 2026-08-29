import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from .base import BaseActionExecutor
from ..types import ActionProposal, ActionResult, ActionResultStatus

logger = logging.getLogger(__name__)

class UnimplementedActionExecutor(BaseActionExecutor):
    """Executor for action intents reserved for future phases.

    Returns NOT_IMPLEMENTED status without fabricating database success.
    """

    async def execute(
        self,
        proposal: ActionProposal,
        user: User,
        db: AsyncSession
    ) -> ActionResult:
        action_name = proposal.intent_type.value.replace("_", " ").title()
        msg = f"I understand the request to {action_name.lower()}, but that action is not available yet in this phase."

        logger.info(f"[AUTO-01 UNIMPLEMENTED ACTION] Intent {proposal.intent_type.value} requested by {user.email}")

        return ActionResult(
            status=ActionResultStatus.NOT_IMPLEMENTED,
            action_type=proposal.intent_type,
            message=msg,
            error_code="ACTION_NOT_IMPLEMENTED"
        )
