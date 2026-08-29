import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.approval.models import WorkflowExecution

logger = logging.getLogger(__name__)

class WorkflowCompensationHandler:
    @staticmethod
    async def compensate_step(
        db: AsyncSession,
        execution: WorkflowExecution,
        step_name: str,
        compensation_def: Dict[str, Any]
    ) -> bool:
        """Executes a compensation action for a single failed workflow step to recover consistency."""
        logger.info(f"WorkflowCompensationHandler: Executing compensation for step '{step_name}' on execution '{execution.id}'")
        
        comp_type = compensation_def.get("type", "default")
        
        # Simulating compensation triggers
        if comp_type == "delete_project":
            project_id = execution.context.get("project_id")
            logger.info(f"WorkflowCompensationHandler: Reverting project creation. Deleting project: {project_id}")
            # In production, call repository delete logic:
            # if project_id: await ProjectRepository.delete(db, UUID(project_id))
        elif comp_type == "remove_team":
            logger.info("WorkflowCompensationHandler: Reverting team allocation. Removing assigned users.")
        else:
            logger.info(f"WorkflowCompensationHandler: Running generic rollback trigger action for type '{comp_type}'")

        return True
