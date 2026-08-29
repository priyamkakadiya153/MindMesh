from app.agents.events import agent_events
from app.agents.communication.protocol import AgentMessage

class MessageEvents:
    @staticmethod
    async def message_sent(message: AgentMessage):
        await agent_events.trigger("message_sent", {
            "message_id": message.message_id,
            "sender": message.sender,
            "receiver": message.receiver,
            "priority": message.priority
        })

    @staticmethod
    async def message_delivered(message: AgentMessage):
        await agent_events.trigger("message_delivered", {
            "message_id": message.message_id,
            "sender": message.sender,
            "receiver": message.receiver
        })
