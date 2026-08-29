from uuid import UUID
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class SharedContext(BaseModel):
    user_id: UUID
    organization_id: UUID
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    
    # Collaborative Agent Space
    memory: Dict[str, Any] = Field(default_factory=dict)
    retrieved_knowledge: List[Dict[str, Any]] = Field(default_factory=list)
    execution_state: Dict[str, Any] = Field(default_factory=dict)
