import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator, List, Union
from dataclasses import dataclass, field
from app.ai.gateway.models import AIRequest, AIResponse, AIStreamEvent, AIResponseStatus, AIUsage, AITiming, AIError

@dataclass
class LLMSettings:
    provider: str = "gemini"
    model: str = "gemini-2.5-flash"
    temperature: float = 0.2
    top_p: float = 0.95
    max_tokens: int = 2048
    fallback_provider: str = "openai"
    fallback_model: str = "gpt-4o-mini"
    system_prompt: Optional[str] = None

@dataclass
class UnifiedLLMResponse:
    content: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    latency_ms: int = 0
    finish_reason: str = "stop"

class ModelProvider(ABC):
    """Provider-independent Model Provider Interface."""

    def __init__(self, provider_name: str, default_model: str):
        self.provider_name = provider_name
        self.default_model = default_model

    @abstractmethod
    async def generate_response(self, request: AIRequest) -> AIResponse:
        """Executes content generation for normalized AIRequest and returns AIResponse."""
        pass

    @abstractmethod
    async def stream_response(self, request: AIRequest) -> AsyncGenerator[AIStreamEvent, None]:
        """Streams response tokens as normalized AIStreamEvent objects."""
        pass

    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        settings: Optional[LLMSettings] = None
    ) -> AsyncGenerator[str, None]:
        """Convenience method wrapping stream_response for token generators."""
        req = AIRequest(
            user_id=None,
            message=prompt,
            system_context=system_prompt,
            generation_parameters={
                "temperature": settings.temperature if settings else 0.2,
                "max_tokens": settings.max_tokens if settings else 1024
            }
        )
        async for evt in self.stream_response(req):
            if evt.type == "TOKEN" and evt.content:
                yield evt.content

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Counts or estimates token count for text."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Checks provider health, connectivity, and latency."""
        pass

# Backward compatibility alias
BaseLLMProvider = ModelProvider
BaseLLMAdapter = ModelProvider
