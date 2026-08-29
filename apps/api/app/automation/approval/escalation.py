import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.approval.models import ApprovalRequest
from app.automation.approval.notifications import ApprovalNotifications
from uuid import UUID

logger = logging.getLogger(__name__)

class ApprovalEscalator:
    @staticmethod
    async def run_escalation_checks(db: AsyncSession):
        """Polls for pending waiting approvals exceeding their SLA hours limit and auto-escalates."""
        logger.info("ApprovalEscalator: Running time-based escalation checking sweep.")
        
        stmt = select(ApprovalRequest).where(
            ApprovalRequest.status == "Waiting"
        )
        res = await db.execute(stmt)
        pending_approvals = res.scalars().all()
        now = datetime.utcnow()

        for approval in pending_approvals:
            limit_hours = approval.sla_limit_hours or 24 # default SLA 24 hours
            elapsed = now - approval.created_at
            
            if elapsed > timedelta(hours=limit_hours):
                logger.warning(f"ApprovalEscalator: Escalation SLA breached for approval request '{approval.title}' (ID: {approval.id})")
                
                # Escalate to owner_id / supervisor or fallback user
                approval.status = "Escalated"
                approval.escalated_at = now
                
                # Assume fallback supervisor ID for escalation
                supervisor_id = "00000000-0000-0000-0000-000000000000"
                approval.escalated_to = supervisor_id
                approval.assigned_approver = supervisor_id
                
                db.add(approval)
                await db.flush()

                try:
                    await ApprovalNotifications.send_approval_requested(
                        db=db,
                        user_id=UUID(supervisor_id),
                        approval_title=f"[ESCALATED] {approval.title}",
                        approval_id=approval.id
                    )
                except ValueError:
                    pass
        await db.commit()
