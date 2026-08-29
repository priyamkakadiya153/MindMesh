import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.governance.policy_store import PolicyStore

logger = logging.getLogger(__name__)

class GovernanceApprovalGate:
    @staticmethod
    async def requires_approval(db: AsyncSession, organization_id: UUID, action_type: str) -> bool:
        """Determines if a given action requires an admin approval gate."""
        policies = await PolicyStore.list_policies(db, organization_id, "Workflow")
        for policy in policies:
            if "require_approval_actions" in policy.rules:
                if action_type in policy.rules["require_approval_actions"]:
                    return True
        return False
