from uuid import UUID
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SessionContext(BaseModel):
    user_id: UUID
    organization_id: UUID
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    permissions: List[str] = Field(default_factory=list)
    request_id: str
    user_role: Optional[str] = None
    additional_context: Dict[str, Any] = Field(default_factory=dict)
