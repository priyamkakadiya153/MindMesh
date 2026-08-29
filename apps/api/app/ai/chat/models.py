from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from uuid import UUID

class TokenUsage(BaseModel):
    prompt: int = Field(..., description="Number of prompt/input tokens used")
    completion: int = Field(..., description="Number of completion/output tokens used")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="AI generated response string")
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Associated document references")
    confidence: float = Field(..., description="Groundedness confidence score")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved raw context details")
    tokens: TokenUsage = Field(..., description="Token breakdown")
    cost: float = Field(..., description="Estimated cost of generation in USD")
    latency_ms: int = Field(..., description="Total execution time in milliseconds")
    suggestions: List[str] = Field(default_factory=list, description="Follow-up question prompts")
    chat_id: Optional[UUID] = Field(default=None, description="Persisted chat session ID if available")

class ChatSessionInfo(BaseModel):
    id: UUID
    organization_id: UUID
    name: Optional[str] = None
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    created_at: Any
    updated_at: Any
