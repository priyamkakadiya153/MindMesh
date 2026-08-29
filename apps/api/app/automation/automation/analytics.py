import logging
from uuid import UUID
from typing import Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.approval.models import WorkflowExecution, ApprovalRequest
from app.automation.workers.monitoring import WorkerQueueMonitor

logger = logging.getLogger(__name__)

class AutomationAnalytics:
    @staticmethod
    async def get_dashboard_summary(db: AsyncSession, organization_id: UUID) -> Dict[str, Any]:
        """Gathers counts and durations representing active and completed pipelines metrics."""
        # 1. Active / Failed Workflows counts
        stmt_execs = select(WorkflowExecution.status, func.count(WorkflowExecution.id)).where(
            WorkflowExecution.organization_id == organization_id
        ).group_by(WorkflowExecution.status)

        res_execs = await db.execute(stmt_execs)
        exec_counts = dict(res_execs.all())

        # 2. Pending approvals count
        stmt_approvals = select(func.count(ApprovalRequest.id)).where(
            ApprovalRequest.organization_id == organization_id,
            ApprovalRequest.status.in_(["Waiting", "Escalated", "Delegated"])
        )
        res_approvals = await db.execute(stmt_approvals)
        pending_approvals = res_approvals.scalar() or 0

        # 3. Retrieve background worker statuses
        worker_health = WorkerQueueMonitor.get_active_worker_stats()

        return {
            "active_workflows": exec_counts.get("Running", 0),
            "pending_approvals": pending_approvals,
            "failed_jobs": exec_counts.get("Failed", 0),
            "completed_workflows": exec_counts.get("Completed", 0),
            "rolled_back_workflows": exec_counts.get("Rolled Back", 0),
            "worker_health": worker_health,
            "sla_status": "Breach Rate: 0.0%",
            "system_status": "Healthy"
        }
