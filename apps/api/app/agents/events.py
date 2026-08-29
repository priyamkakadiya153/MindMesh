import logging
from typing import Callable, Dict, List, Any

logger = logging.getLogger(__name__)

class AgentEvents:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to a specific agent event."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from a specific agent event."""
        if event_type in self._listeners:
            try:
                self._listeners[event_type].remove(callback)
            except ValueError:
                pass

    async def trigger(self, event_type: str, payload: Any):
        """Trigger an event, executing all registered callback hooks."""
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                try:
                    await callback(payload)
                except Exception as e:
                    logger.error(f"Error executing callback for event '{event_type}': {str(e)}", exc_info=True)

# Global event bus
agent_events = AgentEvents()
