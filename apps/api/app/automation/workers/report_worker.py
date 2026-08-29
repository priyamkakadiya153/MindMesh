import logging
import asyncio

logger = logging.getLogger(__name__)

class ReportWorker:
    _loop_task = None
    _running = False

    @classmethod
    def start(cls):
        if cls._running:
            return
        cls._running = True
        cls._loop_task = asyncio.create_task(cls._poll_loop())
        logger.info("ReportWorker: Started background report compile tasks worker.")

    @classmethod
    def stop(cls):
        cls._running = False
        if cls._loop_task:
            cls._loop_task.cancel()
            cls._loop_task = None

    @classmethod
    async def _poll_loop(cls):
        while cls._running:
            # Placeholder for running complex analytics aggregations in off-peak periods
            await asyncio.sleep(10.0)
