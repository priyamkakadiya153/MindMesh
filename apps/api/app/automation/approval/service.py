import logging
from datetime import datetime
from uuid import UUID
from typing import Dict, Any, Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.approval.models import ApprovalRequest
from app.automation.approval.engine import ApprovalEngine
from app.automation.approval.notifications import ApprovalNotifications

logger = logging.getLogger(__name__)

class ApprovalService:
    @staticmethod
    async def create_approval(
        db: AsyncSession,
        workflow_execution_id: Optional[UUID],
        step_name: Optional[str],
        title: str,
        description: Optional[str],
        assigned_approver: Optional[str],
        policy_type: str,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        sla_limit_hours: Optional[int] = None
    ) -> ApprovalRequest:
        """Creates a new human-in-the-loop approval request."""
        approval = ApprovalRequest(
            workflow_execution_id=workflow_execution_id,
            step_name=step_name,
            title=title,
            description=description,
            status="Waiting",
            assigned_approver=assigned_approver,
            policy_type=policy_type,
            approvers_voted={},
            organization_id=organization_id,
            workspace_id=workspace_id,
            sla_limit_hours=sla_limit_hours
        )
        db.add(approval)
        await db.flush()

        # Send request notification to primary approver
        if assigned_approver:
            try:
                approver_uuid = UUID(assigned_approver)
                await ApprovalNotifications.send_approval_requested(db, approver_uuid, title, approval.id)
            except ValueError:
                # E.g. Role based comma-separated approvers
                pass

        return approval

    @staticmethod
    async def get_approval(db: AsyncSession, approval_id: UUID) -> Optional[ApprovalRequest]:
        """Retrieves a single approval by its ID."""
        stmt = select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_approvals(db: AsyncSession, organization_id: UUID, status: Optional[str] = None) -> List[ApprovalRequest]:
        """Lists active or historical approvals for an organization."""
        stmt = select(ApprovalRequest).where(ApprovalRequest.organization_id == organization_id)
        if status:
            stmt = stmt.where(ApprovalRequest.status == status)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def submit_decision(
        db: AsyncSession,
        approval_id: UUID,
        user_id: str,
        vote: str,  # Approved or Rejected
        comments: Optional[str] = None
    ) -> ApprovalRequest:
        """Submits a vote for a human approval request and evaluates workflow progression."""
        approval = await ApprovalService.get_approval(db, approval_id)
        if not approval:
            raise ValueError(f"ApprovalRequest '{approval_id}' not found.")

        if approval.status not in ["Waiting", "Delegated", "Escalated"]:
            raise ValueError(f"ApprovalRequest has already been finalized as '{approval.status}'.")

        # Process vote
        new_status = ApprovalEngine.process_decision(approval, user_id, vote)
        approval.status = new_status
        approval.comments = comments
        approval.updated_at = datetime.utcnow()

        if new_status in ["Approved", "Rejected"]:
            approval.decision_by = user_id
            approval.decision_at = datetime.utcnow()

            # Alert notifications
            try:
                creator_uuid = UUID(user_id)
                await ApprovalNotifications.send_approval_resolved(db, creator_uuid, approval.title, new_status)
            except ValueError:
                pass

            # Resume blocked workflow engine if linked
            if approval.workflow_execution_id:
                from app.automation.workflow.orchestrator import WorkflowOrchestrator
                if new_status == "Approved":
                    # Resume execution
                    await WorkflowOrchestrator.resume_execution(
                        db=db,
                        execution_id=approval.workflow_execution_id,
                        step_name=approval.step_name or "",
                        context_updates={"approval_comments": comments, "approved_by": user_id}
                    )
                else:
                    # Fail/Rollback execution on rejection
                    await WorkflowOrchestrator.fail_execution(
                        db=db,
                        execution_id=approval.workflow_execution_id,
                        error_message=f"Human Approval Rejected by user '{user_id}'. Comments: '{comments}'"
                    )

        db.add(approval)
        await db.flush()
        return approval
