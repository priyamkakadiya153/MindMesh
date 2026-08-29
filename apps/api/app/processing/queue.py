# Task queues definitions manager
import logging

logger = logging.getLogger(__name__)

def enqueue_task(task_name, *args, **kwargs):
    logger.info(f"Task enqueued: {task_name} with arguments: {args} {kwargs}")

class ProcessingQueue:
    @staticmethod
    def enqueue(background_tasks, func, *args, **kwargs):
        logger.info(f"Enqueuing background task: {func.__name__}")
        background_tasks.add_task(func, *args, **kwargs)

