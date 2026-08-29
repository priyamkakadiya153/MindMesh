import logging
from typing import Dict, List, Callable, Awaitable
from app.agents.communication.protocol import AgentMessage

logger = logging.getLogger(__name__)

class MessageBus:
    def __init__(self):
        # Maps receiver name -> list of async handlers
        self._handlers: Dict[str, List[Callable[[AgentMessage], Awaitable[None]]]] = {}
        # Stores global message logs/history
        self.history: List[AgentMessage] = []

    def subscribe(self, receiver_name: str, handler: Callable[[AgentMessage], Awaitable[None]]):
        """Subscribes an async handler to messages routed to a specific agent name."""
        if receiver_name not in self._handlers:
            self._handlers[receiver_name] = []
        self._handlers[receiver_name].append(handler)
        logger.info(f"MessageBus: Subscribed handler for '{receiver_name}'")

    async def publish(self, message: AgentMessage):
        """Publishes a message to target handlers and records history."""
        self.history.append(message)
        logger.info(
            f"MessageBus: Broadcast [{message.priority}] from '{message.sender}' to '{message.receiver}': {message.message_id}"
        )

        handlers = self._handlers.get(message.receiver, [])
        # Also support wildcard receiver subscriptions
        wildcard_handlers = self._handlers.get("*", [])

        all_handlers = handlers + wildcard_handlers
        for handler in all_handlers:
            try:
                await handler(message)
            except Exception as e:
                logger.error(
                    f"MessageBus: Error in handler for '{message.receiver}': {str(e)}",
                    exc_info=True
                )

    def get_history(self, conversation_id: str) -> List[AgentMessage]:
        """Filters message history by conversation ID."""
        return [msg for msg in self.history if msg.conversation_id == conversation_id]

    def clear(self):
        """Resets bus state."""
        self._handlers.clear()
        self.history.clear()

message_bus = MessageBus()
