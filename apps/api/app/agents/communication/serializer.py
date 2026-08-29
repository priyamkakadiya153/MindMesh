import json
from typing import Dict, Any
from app.agents.communication.protocol import AgentMessage

class MessageSerializer:
    @staticmethod
    def serialize(message: AgentMessage) -> str:
        """Serializes AgentMessage instance to a JSON string."""
        return message.model_dump_json()

    @staticmethod
    def deserialize(data_str: str) -> AgentMessage:
        """Deserializes a JSON string back to an AgentMessage instance."""
        data = json.loads(data_str)
        return AgentMessage(**data)
