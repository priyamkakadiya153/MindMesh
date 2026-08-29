from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, List, Optional

class MemoryAddRequest(BaseModel):
    memory_type: str = Field(..., pattern="^(User|Project|Organization|Agent)$")
    scope_key: str = Field(..., max_length=100)
    key: str = Field(..., max_length=100)
    value: Dict[str, Any] = Field(...)
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    importance_score: Optional[float] = 0.5
    confidence_score: Optional[float] = 1.0
    retention_days: Optional[int] = None

class MemorySearchRequest(BaseModel):
    query_key: Optional[str] = None
    project_id: Optional[UUID] = None
    workspace_id: Optional[UUID] = None

class MemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    memory_type: str
    scope_key: str
    organization_id: UUID
    workspace_id: Optional[UUID]
    project_id: Optional[UUID]
    key: str
    value: Dict[str, Any]
    importance_score: float
    confidence_score: float
    retention_expires_at: Optional[datetime]
    last_accessed_at: datetime
    created_at: datetime

class FeedbackSubmitRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    execution_id: Optional[UUID] = None
    comment: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None

class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    execution_id: Optional[UUID]
    user_id: UUID
    organization_id: UUID
    feedback_type: str
    rating: int
    comment: Optional[str]
    context_data: Optional[Dict[str, Any]]
    processed: bool
    created_at: datetime

class PolicyCreateRequest(BaseModel):
    name: str = Field(..., max_length=100)
    category: str = Field(..., pattern="^(Security|Data|Memory|Workflow|Tool|Compliance|Privacy)$")
    rules: Dict[str, Any] = Field(...)

class PolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    category: str
    rules: Dict[str, Any]
    is_active: bool
    created_at: datetime

class PolicyValidateRequest(BaseModel):
    category: str = Field(..., pattern="^(Security|Data|Memory|Workflow|Tool|Compliance|Privacy)$")
    context_data: Dict[str, Any] = Field(...)

class PolicyValidateResponse(BaseModel):
    is_allowed: bool
    violations: List[str]
