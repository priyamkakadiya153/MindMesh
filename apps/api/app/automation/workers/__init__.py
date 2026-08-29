import logging
from app.automation.workers.workflow_worker import WorkflowWorker
from app.automation.workers.scheduler_worker import SchedulerWorker
from app.automation.workers.ai_worker import AIWorker
from app.automation.workers.cleanup_worker import CleanupWorker
from app.automation.workers.notification_worker import NotificationWorker
from app.automation.workers.report_worker import ReportWorker
from app.automation.workers.monitoring import WorkerQueueMonitor

logger = logging.getLogger(__name__)

class BackgroundWorkerManager:
    _is_active = False

    @classmethod
    def start_all(cls):
        """Starts all background worker threads/tasks loop processes."""
        if cls._is_active:
            return
        WorkflowWorker.start()
        SchedulerWorker.start()
        AIWorker.start()
        CleanupWorker.start()
        NotificationWorker.start()
        ReportWorker.start()
        WorkerQueueMonitor.start()
        cls._is_active = True
        logger.info("BackgroundWorkerManager: Successfully initialized all automation daemon workers.")

    @classmethod
    def stop_all(cls):
        """Cleanly cancels and shuts down all active background daemon workers."""
        if not cls._is_active:
            return
        WorkflowWorker.stop()
        SchedulerWorker.stop()
        AIWorker.stop()
        CleanupWorker.stop()
        NotificationWorker.stop()
        ReportWorker.stop()
        WorkerQueueMonitor.stop()
        cls._is_active = False
        logger.info("BackgroundWorkerManager: Successfully terminated all active daemon workers.")

__all__ = [
    "BackgroundWorkerManager",
    "WorkflowWorker",
    "SchedulerWorker",
    "AIWorker",
    "CleanupWorker",
    "NotificationWorker",
    "ReportWorker",
    "WorkerQueueMonitor"
]
