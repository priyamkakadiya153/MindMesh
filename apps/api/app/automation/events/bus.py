import logging
from typing import Dict, List, Callable, Any, Awaitable

logger = logging.getLogger(__name__)

# Callback type representing an async event subscriber handler
EventCallback = Callable[[str, Dict[str, Any]], Awaitable[None]]

class EventBus:
    def __init__(self):
        self._listeners: Dict[str, List[EventCallback]] = {}

    def subscribe(self, event_type: str, callback: EventCallback):
        """Subscribes an async callback to a specific event type."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
        logger.info(f"EventBus: Registered subscription for event '{event_type}'")

    async def publish(self, event_type: str, payload: Dict[str, Any]):
        """Publishes an event to all active listeners."""
        logger.info(f"EventBus: Publishing event '{event_type}' with payload: {payload}")
        callbacks = self._listeners.get(event_type, [])
        # Also support wildcard listeners
        callbacks.extend(self._listeners.get("*", []))

        for cb in callbacks:
            try:
                await cb(event_type, payload)
            except Exception as e:
                logger.error(f"EventBus: Error executing handler for event '{event_type}': {str(e)}", exc_info=True)

    def clear(self):
        """Clears all listeners."""
        self._listeners.clear()

event_bus = EventBus()
