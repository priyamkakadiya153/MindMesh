import logging
from uuid import UUID
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.approval.models import WorkflowExecution
from app.automation.workflow.engine import WorkflowEngine
from app.automation.workflow.lifecycle import WorkflowLifecycle
from app.automation.workflow.rollback import WorkflowRollbackCoordinator

logger = logging.getLogger(__name__)

class WorkflowOrchestrator:
    @staticmethod
    async def start_execution(
        db: AsyncSession,
        workflow_id: UUID,
        initial_context: Dict[str, Any],
        organization_id: UUID,
        workspace_id: Optional[UUID] = None
    ) -> WorkflowExecution:
        """Spawns and executes a new workflow instance."""
        logger.info(f"WorkflowOrchestrator: Spawning workflow execution for definition ID: {workflow_id}")
        
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status="Draft",
            context=initial_context,
            current_step_index=0,
            organization_id=organization_id,
            workspace_id=workspace_id
        )
        db.add(execution)
        await db.flush()

        # Run immediately using engine
        await WorkflowEngine.execute_workflow(db, execution)
        return execution

    @staticmethod
    async def resume_execution(
        db: AsyncSession,
        execution_id: UUID,
        step_name: str,
        context_updates: Dict[str, Any]
    ) -> Optional[WorkflowExecution]:
        """Resumes a paused execution (triggered by external inputs or human approvals)."""
        logger.info(f"WorkflowOrchestrator: Resuming paused execution: {execution_id}")
        
        stmt = select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
        res = await db.execute(stmt)
        execution = res.scalar_one_or_none()

        if not execution:
            logger.error(f"WorkflowOrchestrator: Execution '{execution_id}' not found.")
            return None

        await WorkflowEngine.resume_workflow(db, execution, step_name, context_updates)
        return execution

    @staticmethod
    async def fail_execution(
        db: AsyncSession,
        execution_id: UUID,
        error_message: str
    ) -> Optional[WorkflowExecution]:
        """Aborts workflow execution and triggers compensation rollback."""
        logger.info(f"WorkflowOrchestrator: Force failing execution {execution_id} due to: {error_message}")
        
        stmt = select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
        res = await db.execute(stmt)
        execution = res.scalar_one_or_none()

        if not execution:
            return None

        await WorkflowLifecycle.fail_execution(db, execution, error_message)
        await WorkflowRollbackCoordinator.trigger_rollback(db, execution)
        return execution

    @staticmethod
    async def cancel_execution(
        db: AsyncSession,
        execution_id: UUID
    ) -> Optional[WorkflowExecution]:
        """Cancels a workflow execution."""
        logger.info(f"WorkflowOrchestrator: Cancelling execution {execution_id}")
        
        stmt = select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
        res = await db.execute(stmt)
        execution = res.scalar_one_or_none()

        if not execution:
            return None

        await WorkflowLifecycle.cancel_execution(db, execution)
        return execution
