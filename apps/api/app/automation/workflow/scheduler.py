import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.approval.models import WorkflowSchedule
from app.automation.workflow.orchestrator import WorkflowOrchestrator

logger = logging.getLogger(__name__)

class WorkflowScheduler:
    @staticmethod
    def calculate_next_run(expression: str, now: datetime) -> datetime:
        """Calculates next run datetime from cron expression or interval in seconds."""
        if expression.isdigit():
            # Seconds interval
            return now + timedelta(seconds=int(expression))
        
        # Default fallback to daily scheduler for cron syntax
        return now + timedelta(days=1)

    @staticmethod
    async def run_scheduler_sweep(db: AsyncSession):
        """Polls scheduled workflows and executes those that are due, then recalculates next_run_at."""
        logger.info("WorkflowScheduler: Running scheduled workflows sweep check.")
        now = datetime.utcnow()

        stmt = select(WorkflowSchedule)
        res = await db.execute(stmt)
        schedules = res.scalars().all()

        for sched in schedules:
            if sched.next_run_at <= now:
                logger.info(f"WorkflowScheduler: Triggering scheduled execution for workflow ID: {sched.workflow_id}")
                
                try:
                    # Spawn workflow execution
                    await WorkflowOrchestrator.start_execution(
                        db=db,
                        workflow_id=sched.workflow_id,
                        initial_context={"scheduled_trigger": True, "triggered_at": now.isoformat()},
                        organization_id=sched.organization_id,
                        workspace_id=sched.workspace_id
                    )
                except Exception as e:
                    logger.error(f"WorkflowScheduler: Failed to start execution for scheduled workflow {sched.workflow_id}: {str(e)}")

                # Recalculate next execution time
                sched.next_run_at = WorkflowScheduler.calculate_next_run(sched.expression, now)
                db.add(sched)
                await db.flush()

        await db.commit()
Defined: "WorkflowScheduler.run_scheduler_sweep"
