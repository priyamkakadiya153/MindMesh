import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

class AIResponseStatus(str, Enum):
    DRAFT = "DRAFT"
    SENDING = "SENDING"
    SENT = "SENT"
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    STREAMING = "STREAMING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class AIRequestLifecycle(str, Enum):
    REQUESTED = "REQUESTED"
    VALIDATED = "VALIDATED"
    PROCESSING = "PROCESSING"
    MODEL_INVOCATION = "MODEL_INVOCATION"
    RESPONSE_NORMALIZATION = "RESPONSE_NORMALIZATION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@dataclass
class AIUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0

@dataclass
class AITiming:
    request_start_time: float = 0.0
    provider_start_time: float = 0.0
    first_token_time: float = 0.0
    completion_time: float = 0.0
    total_latency_ms: int = 0
    provider_latency_ms: int = 0

@dataclass
class AIError:
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

@dataclass
class AIRequest:
    """Normalized internal AI Request Model."""
    user_id: uuid.UUID
    message: str
    request_id: uuid.UUID = field(default_factory=uuid.uuid4)
    idempotency_key: Optional[str] = None
    conversation_id: Optional[uuid.UUID] = None
    workspace_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    conversation_context: List[Dict[str, Any]] = field(default_factory=list)
    system_context: Optional[str] = None
    model_preferences: Dict[str, Any] = field(default_factory=dict)
    generation_parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GenerationAttempt:
    """Tracks a single execution attempt to generate an AI response."""
    generation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    request_id: uuid.UUID = field(default_factory=uuid.uuid4)
    conversation_id: Optional[uuid.UUID] = None
    user_message_id: Optional[uuid.UUID] = None
    assistant_message_id: Optional[uuid.UUID] = None
    provider: str = "gemini"
    model: str = "gemini-2.5-flash"
    status: AIResponseStatus = AIResponseStatus.PENDING
    started_at: float = field(default_factory=dict)
    completed_at: Optional[float] = None
    error_category: Optional[str] = None

@dataclass
class AIResponse:
    """Normalized internal AI Response Model."""
    request_id: uuid.UUID
    content: str
    status: AIResponseStatus = AIResponseStatus.COMPLETED
    response_id: uuid.UUID = field(default_factory=uuid.uuid4)
    generation_id: Optional[uuid.UUID] = None
    user_message_id: Optional[uuid.UUID] = None
    conversation_id: Optional[uuid.UUID] = None
    model: str = "gemini-2.5-flash"
    provider: str = "gemini"
    usage: AIUsage = field(default_factory=AIUsage)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timing: AITiming = field(default_factory=AITiming)
    error: Optional[AIError] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response_id": str(self.response_id),
            "request_id": str(self.request_id),
            "generation_id": str(self.generation_id) if self.generation_id else None,
            "user_message_id": str(self.user_message_id) if self.user_message_id else None,
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "content": self.content,
            "status": self.status.value,
            "model": self.model,
            "provider": self.provider,
            "usage": {
                "prompt_tokens": self.usage.prompt_tokens,
                "completion_tokens": self.usage.completion_tokens,
                "total_tokens": self.usage.total_tokens,
                "estimated_cost_usd": self.usage.estimated_cost_usd,
            },
            "sources": self.sources,
            "metadata": self.metadata if isinstance(self.metadata, dict) else {},
            "timing": {
                "total_latency_ms": self.timing.total_latency_ms,
                "provider_latency_ms": self.timing.provider_latency_ms,
            },
            "error": {
                "code": self.error.code,
                "message": self.error.message,
                "details": self.error.details,
            } if self.error else None,
        }

@dataclass
class AIStreamEvent:
    """Normalized stream event payload for SSE and real-time gateways."""
    type: str  # START, DELTA, TOKEN, STATUS, COMPLETE, ERROR, CANCELLED
    content: str = ""
    request_id: Optional[str] = None
    generation_id: Optional[str] = None
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
