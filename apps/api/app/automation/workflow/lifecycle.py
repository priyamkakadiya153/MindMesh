import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.approval.models import WorkflowExecution
from app.automation.workflow.events import WorkflowEvents

logger = logging.getLogger(__name__)

class WorkflowLifecycle:
    @staticmethod
    async def start_execution(db: AsyncSession, execution: WorkflowExecution):
        """Starts a workflow execution, setting status to Running."""
        execution.status = "Running"
        execution.started_at = datetime.utcnow()
        db.add(execution)
        await db.flush()

        logger.info(f"WorkflowLifecycle: Execution '{execution.id}' started running.")
        await WorkflowEvents.execution_started(execution)

    @staticmethod
    async def complete_execution(db: AsyncSession, execution: WorkflowExecution):
        """Finalizes execution, setting status to Completed."""
        execution.status = "Completed"
        execution.completed_at = datetime.utcnow()
        db.add(execution)
        await db.flush()

        logger.info(f"WorkflowLifecycle: Execution '{execution.id}' completed successfully.")
        await WorkflowEvents.execution_completed(execution)

    @staticmethod
    async def fail_execution(db: AsyncSession, execution: WorkflowExecution, error: str):
        """Fails execution, setting status to Failed."""
        execution.status = "Failed"
        execution.completed_at = datetime.utcnow()
        execution.error = error
        db.add(execution)
        await db.flush()

        logger.error(f"WorkflowLifecycle: Execution '{execution.id}' failed: {error}")
        await WorkflowEvents.execution_failed(execution, error)

    @staticmethod
    async def cancel_execution(db: AsyncSession, execution: WorkflowExecution):
        """Cancels a running or waiting workflow execution."""
        execution.status = "Cancelled"
        execution.completed_at = datetime.utcnow()
        db.add(execution)
        await db.flush()

        logger.info(f"WorkflowLifecycle: Execution '{execution.id}' was cancelled by request.")
        # Trigger any cleanup/event notification
