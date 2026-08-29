import logging
from uuid import UUID
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.approval.models import WorkflowDefinition, WorkflowExecution, WorkflowSchedule
from app.automation.automation.repository import AutomationRepository
from app.automation.workflow.validator import WorkflowValidator
from app.automation.workflow.orchestrator import WorkflowOrchestrator
from app.automation.workflow.scheduler import WorkflowScheduler

logger = logging.getLogger(__name__)

class AutomationService:
    @staticmethod
    async def create_workflow(
        db: AsyncSession,
        name: str,
        description: Optional[str],
        definition: Dict[str, Any],
        organization_id: UUID,
        workspace_id: Optional[UUID] = None
    ) -> WorkflowDefinition:
        """Validates, creates, and registers workflow schedules automatically."""
        # 1. Schema Validation
        errors = WorkflowValidator.validate_definition(definition)
        if errors:
            raise ValueError(f"Workflow validation failed: {'; '.join(errors)}")

        # 2. Persist Workflow definition
        wdef = WorkflowDefinition(
            name=name,
            description=description,
            definition=definition,
            version=1,
            organization_id=organization_id,
            workspace_id=workspace_id
        )
        wdef = await AutomationRepository.create_workflow(db, wdef)

        # 3. Setup Scheduler record if trigger is schedule
        trigger = definition.get("trigger", {})
        if trigger.get("type") == "schedule":
            schedule_type = trigger.get("schedule_type", "cron")
            expression = trigger.get("expression", "86400") # default daily in seconds

            next_run = WorkflowScheduler.calculate_next_run(expression, datetime.utcnow())

            schedule = WorkflowSchedule(
                workflow_id=wdef.id,
                schedule_type=schedule_type,
                expression=expression,
                next_run_at=next_run,
                organization_id=organization_id,
                workspace_id=workspace_id
            )
            db.add(schedule)
            await db.flush()

        await db.commit()
        return wdef

    @staticmethod
    async def trigger_workflow(
        db: AsyncSession,
        workflow_id: UUID,
        initial_context: Dict[str, Any],
        organization_id: UUID,
        workspace_id: Optional[UUID] = None
    ) -> WorkflowExecution:
        """Explicitly triggers a workflow execution."""
        execution = await WorkflowOrchestrator.start_execution(
            db=db,
            workflow_id=workflow_id,
            initial_context=initial_context,
            organization_id=organization_id,
            workspace_id=workspace_id
        )
        await db.commit()
        return execution

    @staticmethod
    async def cancel_workflow(db: AsyncSession, execution_id: UUID) -> Optional[WorkflowExecution]:
        """Cancels a running workflow execution."""
        execution = await WorkflowOrchestrator.cancel_execution(db, execution_id)
        await db.commit()
        return execution
