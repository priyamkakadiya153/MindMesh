import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.notifications.models import Notification

logger = logging.getLogger(__name__)

class ApprovalNotifications:
    @staticmethod
    async def send_approval_requested(
        db: AsyncSession,
        user_id: UUID,
        approval_title: str,
        approval_id: UUID
    ):
        """Sends a notification that an approval has been requested."""
        logger.info(f"ApprovalNotifications: Sending request notification to user '{user_id}' for approval: {approval_title}")
        try:
            notif = Notification(
                user_id=user_id,
                title="Action Required: Approval Needed",
                message=f"You have been assigned to review and decide on the approval: '{approval_title}'. ID: {approval_id}",
                type="approval_required",
                priority="high",
                is_read=False
            )
            db.add(notif)
            await db.flush()
        except Exception as e:
            logger.error(f"ApprovalNotifications: Error saving request notification: {str(e)}")

    @staticmethod
    async def send_approval_resolved(
        db: AsyncSession,
        user_id: UUID,
        approval_title: str,
        status: str
    ):
        """Sends a notification that an approval request has been resolved (Approved/Rejected)."""
        logger.info(f"ApprovalNotifications: Sending resolution notification to user '{user_id}': '{approval_title}' is {status}")
        try:
            notif = Notification(
                user_id=user_id,
                title=f"Approval Request {status}",
                message=f"The approval request '{approval_title}' has been successfully resolved as: '{status}'.",
                type="approval_resolved",
                priority="normal",
                is_read=False
            )
            db.add(notif)
            await db.flush()
        except Exception as e:
            logger.error(f"ApprovalNotifications: Error saving resolution notification: {str(e)}")
