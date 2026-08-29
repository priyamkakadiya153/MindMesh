import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DefaultEventHandlers:
    @staticmethod
    async def handle_document_upload(event_type: str, payload: Dict[str, Any]):
        """Processes document upload events (e.g., triggers index or OCR workflows)."""
        logger.info(f"DefaultEventHandlers: Received document upload hook event. Payload: {payload}")

    @staticmethod
    async def handle_project_create(event_type: str, payload: Dict[str, Any]):
        """Triggered upon project creations."""
        logger.info(f"DefaultEventHandlers: Received project creation hook event. Payload: {payload}")
