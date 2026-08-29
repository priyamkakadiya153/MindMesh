import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class AgentMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: str
    receiver: str
    task_id: Optional[str] = None
    conversation_id: Optional[str] = None
    priority: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    payload: Dict[str, Any] = Field(default_factory=dict)
