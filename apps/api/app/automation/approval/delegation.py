import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.approval.models import ApprovalRequest
from app.automation.approval.notifications import ApprovalNotifications
from uuid import UUID

logger = logging.getLogger(__name__)

class ApprovalDelegator:
    @staticmethod
    async def delegate(
        db: AsyncSession,
        approval: ApprovalRequest,
        delegate_user_id: str
    ):
        """Delegates approval authority from original approver to a new delegate user."""
        logger.info(f"ApprovalDelegator: Delegating approval {approval.id} to user {delegate_user_id}")
        
        approval.delegated_to = delegate_user_id
        approval.assigned_approver = delegate_user_id
        approval.status = "Delegated"
        approval.updated_at = datetime.utcnow()

        db.add(approval)
        await db.flush()

        # Alert the new approver
        try:
            target_uuid = UUID(delegate_user_id)
            await ApprovalNotifications.send_approval_requested(db, target_uuid, approval.title, approval.id)
        except ValueError:
            pass
