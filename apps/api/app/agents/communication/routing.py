import logging
from app.agents.communication.protocol import AgentMessage
from app.agents.communication.message_bus import message_bus
from app.agents.communication.events import MessageEvents

logger = logging.getLogger(__name__)

class MessageRouter:
    @staticmethod
    async def route_message(message: AgentMessage):
        """Routes message dynamically to appropriate agents via the central MessageBus."""
        logger.info(f"MessageRouter: Routing message {message.message_id} to '{message.receiver}'")
        
        # Trigger sending event hook
        await MessageEvents.message_sent(message)
        
        # Deliver to bus
        await message_bus.publish(message)
        
        # Trigger delivery event hook
        await MessageEvents.message_delivered(message)
