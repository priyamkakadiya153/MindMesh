from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

# ---------------- CONVERSATION SCHEMAS ----------------

class ConversationCreateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Conversation title")
    description: Optional[str] = Field(None, description="Optional conversation description")
    workspace_id: Optional[UUID] = Field(None, description="Target workspace UUID")

class ConversationUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_pinned: Optional[bool] = None
    status: Optional[str] = None
    workspace_id: Optional[UUID] = None
    settings: Optional[Dict[str, Any]] = None

class ConversationPinRequest(BaseModel):
    is_pinned: bool = Field(True, description="Pin or unpin status")

class ConversationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    workspace_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    is_pinned: bool = False
    status: str = "active"
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class PaginatedConversationsResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int
    page: int
    limit: int
    total_pages: int

# ---------------- MESSAGE SCHEMAS ----------------

class MessageCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Message text content")
    role: Optional[str] = Field("user", description="'user', 'assistant', or 'system'")
    content_type: Optional[str] = Field("text/plain", description="MIME type e.g. text/plain")
    model: Optional[str] = Field(None, description="AI model used if assistant reply")
    token_count: Optional[int] = Field(0)
    latency_ms: Optional[int] = Field(0)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional JSON metadata")

class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    content_type: str = "text/plain"
    model: Optional[str] = None
    token_count: int = 0
    latency_ms: int = 0
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

# ---------------- LEGACY & RAG SCHEMAS ----------------

class ChatQueryRequest(BaseModel):
    query: Optional[str] = Field(None)
    message: Optional[str] = Field(None)
    chat_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    provider: Optional[str] = "gemini"
    model: Optional[str] = "gemini-2.5-flash"
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 1024
    top_p: Optional[float] = 0.95
    system_prompt: Optional[str] = None
    stream: Optional[bool] = False

class AIRequest(BaseModel):
    user_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    workspace_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    message: str = Field(..., min_length=1)
    provider: Optional[str] = "gemini"
    model: Optional[str] = "gemini-2.5-flash"
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 1024
    stream: Optional[bool] = False

class AIResponse(BaseModel):
    answer: str
    conversation_id: UUID
    sources: List[Dict[str, Any]] = []
    citations: List[Dict[str, Any]] = []
    grounded: bool = True
    confidence: float = 1.0
    provider: str = "gemini"
    model: str = "gemini-2.5-flash"
    intent: Optional[str] = "GENERAL_KNOWLEDGE"
    metadata: Optional[Dict[str, Any]] = None

class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    provider: Optional[str] = "gemini"
    model: Optional[str] = "gemini-2.0-flash"

class ChatRenameRequest(BaseModel):
    title: str = Field(..., min_length=1)

class ChatUpdateRequest(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None
    workspace_id: Optional[UUID] = None
    settings: Optional[Dict[str, Any]] = None

class ChatExportRequest(BaseModel):
    format: str = Field("markdown", description="Output format: markdown or json")

class CitationSchema(BaseModel):
    id: Optional[UUID] = None
    document: Optional[str] = "Document"
    document_id: UUID
    chunk_id: Optional[UUID] = None
    page: Optional[int] = None
    page_number: Optional[int] = None
    section: Optional[str] = None
    confidence: Optional[float] = 1.0
    score: Optional[float] = 1.0

class ChatMessageSchema(BaseModel):
    id: UUID
    role: str
    content: str
    model: Optional[str] = None
    token_count: Optional[int] = 0
    latency_ms: Optional[int] = 0
    created_at: Optional[datetime] = None
    citations: List[CitationSchema] = []

class ChatHistoryItem(BaseModel):
    id: UUID
    title: str
    snippet: Optional[str] = ""
    is_pinned: bool = False
    workspace_id: Optional[UUID] = None
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

class ChatDetailsResponse(BaseModel):
    id: UUID
    title: str
    organization_id: UUID
    workspace_id: Optional[UUID] = None
    is_pinned: bool = False
    settings: Optional[Dict[str, Any]] = {}
    messages: List[ChatMessageSchema] = []
    created_at: datetime
    updated_at: datetime
