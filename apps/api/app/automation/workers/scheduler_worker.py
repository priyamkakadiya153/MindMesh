import logging
import asyncio
from app.core.database import AsyncSessionLocal
from app.automation.workflow.scheduler import WorkflowScheduler
from app.agents.cognitive_triggers import CognitiveAgentTriggerService

logger = logging.getLogger(__name__)

class SchedulerWorker:
    _loop_task = None
    _running = False

    @classmethod
    def start(cls):
        """Starts the background scheduler polling loop."""
        if cls._running:
            return
        cls._running = True
        cls._loop_task = asyncio.create_task(cls._poll_loop())
        logger.info("SchedulerWorker: Started background scheduler task.")

    @classmethod
    def stop(cls):
        """Stops the scheduler loop."""
        cls._running = False
        if cls._loop_task:
            cls._loop_task.cancel()
            cls._loop_task = None

    @classmethod
    async def _poll_loop(cls):
        """Polls database for ready schedule events."""
        while cls._running:
            try:
                async with AsyncSessionLocal() as db:
                    await WorkflowScheduler.run_scheduler_sweep(db)
                    await CognitiveAgentTriggerService.run_scheduled_trigger_sweep(db)
            except Exception as e:
                logger.error(f"SchedulerWorker: Error executing scheduler sweep: {str(e)}", exc_info=True)
            await asyncio.sleep(2.0)

