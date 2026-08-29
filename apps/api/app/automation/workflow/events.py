import logging
from app.automation.events.bus import event_bus
from app.automation.approval.models import WorkflowExecution

logger = logging.getLogger(__name__)

class WorkflowEvents:
    @staticmethod
    async def execution_started(execution: WorkflowExecution):
        """Emits event when a workflow starts executing."""
        await event_bus.publish("workflow_started", {
            "execution_id": str(execution.id),
            "workflow_id": str(execution.workflow_id),
            "organization_id": str(execution.organization_id)
        })

    @staticmethod
    async def execution_completed(execution: WorkflowExecution):
        """Emits event when a workflow completes successfully."""
        await event_bus.publish("workflow_completed", {
            "execution_id": str(execution.id),
            "workflow_id": str(execution.workflow_id),
            "organization_id": str(execution.organization_id),
            "status": "Completed"
        })

    @staticmethod
    async def execution_failed(execution: WorkflowExecution, error: str):
        """Emits event when a workflow execution fails."""
        await event_bus.publish("workflow_failed", {
            "execution_id": str(execution.id),
            "workflow_id": str(execution.workflow_id),
            "organization_id": str(execution.organization_id),
            "status": "Failed",
            "error": error
        })
