import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import delete
from app.core.database import AsyncSessionLocal
from app.automation.approval.models import AutomationEventLog

logger = logging.getLogger(__name__)

class CleanupWorker:
    _loop_task = None
    _running = False

    @classmethod
    def start(cls):
        if cls._running:
            return
        cls._running = True
        cls._loop_task = asyncio.create_task(cls._poll_loop())
        logger.info("CleanupWorker: Started background storage cleanup worker.")

    @classmethod
    def stop(cls):
        cls._running = False
        if cls._loop_task:
            cls._loop_task.cancel()
            cls._loop_task = None

    @classmethod
    async def _poll_loop(cls):
        while cls._running:
            try:
                await cls.purge_processed_event_logs()
            except Exception as e:
                logger.error(f"CleanupWorker: Purge logs task failed: {str(e)}")
            # Runs cleanup task every 1 hour (3600 seconds)
            await asyncio.sleep(3600.0)

    @classmethod
    async def purge_processed_event_logs(cls):
        """Purges event log records older than 30 days that have been processed."""
        async with AsyncSessionLocal() as db:
            threshold = datetime.utcnow() - timedelta(days=30)
            stmt = delete(AutomationEventLog).where(
                AutomationEventLog.processed == True,
                AutomationEventLog.created_at <= threshold
            )
            await db.execute(stmt)
            await db.commit()
            logger.info("CleanupWorker: Cleaned up old processed event log history.")
            
class_name = "CleanupWorker"
