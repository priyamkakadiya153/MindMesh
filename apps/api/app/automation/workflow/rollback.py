import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.approval.models import WorkflowExecution, WorkflowStepExecution, WorkflowDefinition
from app.automation.workflow.compensation import WorkflowCompensationHandler

logger = logging.getLogger(__name__)

class WorkflowRollbackCoordinator:
    @staticmethod
    async def trigger_rollback(db: AsyncSession, execution: WorkflowExecution):
        """Rolls back all successfully executed steps in reverse order (SAGA orchestration)."""
        logger.info(f"WorkflowRollbackCoordinator: Initiating rollback saga for execution '{execution.id}'")

        # 1. Fetch completed step logs in reverse order
        stmt = select(WorkflowStepExecution).where(
            WorkflowStepExecution.execution_id == execution.id,
            WorkflowStepExecution.status == "Completed"
        ).order_by(WorkflowStepExecution.started_at.desc())

        res = await db.execute(stmt)
        completed_steps = res.scalars().all()

        # Get workflow definition
        stmt_def = select(WorkflowDefinition).where(WorkflowDefinition.id == execution.workflow_id)
        res_def = await db.execute(stmt_def)
        wdef = res_def.scalar_one_or_none()

        if not wdef:
            logger.error(f"WorkflowRollbackCoordinator: Definition not found for rollback of execution {execution.id}")
            return

        steps_list = wdef.definition.get("steps", [])
        steps_map = {step["name"]: step for step in steps_list if "name" in step}

        for step_log in completed_steps:
            step_def = steps_map.get(step_log.step_name, {})
            compensation_def = step_def.get("compensation_step")

            if compensation_def:
                try:
                    await WorkflowCompensationHandler.compensate_step(
                        db=db,
                        execution=execution,
                        step_name=step_log.step_name,
                        compensation_def=compensation_def
                    )
                    step_log.status = "Rolled Back"
                    db.add(step_log)
                    await db.flush()
                except Exception as e:
                    logger.error(f"WorkflowRollbackCoordinator: Failed to execute compensation for step '{step_log.step_name}': {str(e)}")

        execution.status = "Rolled Back"
        db.add(execution)
        await db.flush()
        logger.info(f"WorkflowRollbackCoordinator: Rollback completed for execution '{execution.id}'")
        await db.commit()
