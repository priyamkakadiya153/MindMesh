# Cron scheduler utilities for processing queue
import logging

logger = logging.getLogger(__name__)

def schedule_cleanups():
    logger.info("Initializing background temporary documents cleanup schedules.")
    return True
