import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class EventRegistry:
    # Set of standard built-in events
    EVENT_CATALOG = {
        "document_uploaded",
        "project_created",
        "user_registered",
        "task_completed",
        "workflow_completed",
        "ai_response_generated",
        "search_executed",
        "external_webhook"
    }

    @classmethod
    def is_valid_event(cls, event_type: str) -> bool:
        """Validates if an event type is within the catalog or custom namespace."""
        return event_type in cls.EVENT_CATALOG or event_type.startswith("custom_")

event_registry = EventRegistry()
