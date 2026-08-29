import logging
from typing import Dict, List, Callable, Awaitable, Any
from app.automation.events.bus import event_bus, EventCallback

logger = logging.getLogger(__name__)

class EventSubscriberManager:
    @staticmethod
    def register_listener(event_type: str, callback: EventCallback):
        """Registers a listener to receive messages from the bus."""
        event_bus.subscribe(event_type, callback)

    @staticmethod
    def register_listeners_dict(mapping: Dict[str, EventCallback]):
        """Helper to register multiple listeners at once."""
        for etype, callback in mapping.items():
            event_bus.subscribe(etype, callback)
