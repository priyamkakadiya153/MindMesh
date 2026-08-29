import logging
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.automation.approval.models import WorkflowExecution
from app.automation.workflow.engine import WorkflowEngine

logger = logging.getLogger(__name__)

class WorkflowWorker:
    _loop_task = None
    _running = False

    @classmethod
    def start(cls):
        """Starts the background workflow polling execution thread task."""
        if cls._running:
            return
        cls._running = True
        cls._loop_task = asyncio.create_task(cls._poll_loop())
        logger.info("WorkflowWorker: Started background execution polling worker task.")

    @classmethod
    def stop(cls):
        """Stops the polling loop."""
        cls._running = False
        if cls._loop_task:
            cls._loop_task.cancel()
            cls._loop_task = None

    @classmethod
    async def _poll_loop(cls):
        """Background coroutine loop that periodically checks for workflows in Running state."""
        while cls._running:
            try:
                await cls.process_running_workflows()
            except Exception as e:
                logger.error(f"WorkflowWorker: Polling loop encountered error: {str(e)}", exc_info=True)
            await asyncio.sleep(2.0)

    @classmethod
    async def process_running_workflows(cls):
        """Finds and executes any active running workflow executions."""
        async with AsyncSessionLocal() as db:
            stmt = select(WorkflowExecution).where(WorkflowExecution.status == "Running")
            res = await db.execute(stmt)
            running_list = res.scalars().all()

            for execution in running_list:
                logger.info(f"WorkflowWorker: Processing execution ID {execution.id}")
                try:
                    await WorkflowEngine.execute_workflow(db, execution)
                except Exception as e:
                    logger.error(f"WorkflowWorker: Failed to process execution {execution.id}: {str(e)}")
