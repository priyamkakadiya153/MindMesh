import asyncio
import time
import uuid
import logging
from typing import Dict, Any, AsyncGenerator, List, Optional
from app.ai.llm.base import ModelProvider, UnifiedLLMResponse
from app.ai.gateway.models import (
    AIRequest,
    AIResponse,
    AIResponseStatus,
    AIUsage,
    AITiming,
    AIStreamEvent,
    AIError
)

logger = logging.getLogger(__name__)

class MockModelProvider(ModelProvider):
    """
    Deterministic Mock Model Provider.
    Used for automated unit and contract testing without requiring external LLM API access or quota.
    """

    def __init__(self, model_name: str = "mock-model", fail_mode: bool = False, timeout_mode: bool = False):
        super().__init__(provider_name="mock", default_model=model_name)
        self.model_name = model_name
        self.fail_mode = fail_mode
        self.timeout_mode = timeout_mode

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return int(max(len(text.split()) * 1.3, len(text) / 4))

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if not self.fail_mode else "unhealthy",
            "provider": "mock",
            "model": self.model_name,
            "latency_ms": 5
        }

    async def generate_response(self, request: AIRequest) -> AIResponse:
        start_time = time.time()
        
        if self.timeout_mode:
            await asyncio.sleep(0.5)
            return AIResponse(
                request_id=request.request_id,
                conversation_id=request.conversation_id,
                content="",
                status=AIResponseStatus.FAILED,
                model=self.model_name,
                provider=self.provider_name,
                error=AIError(code="MODEL_TIMEOUT", message="Request timed out during model generation.")
            )

        if self.fail_mode:
            return AIResponse(
                request_id=request.request_id,
                conversation_id=request.conversation_id,
                content="",
                status=AIResponseStatus.FAILED,
                model=self.model_name,
                provider=self.provider_name,
                error=AIError(code="GENERATION_FAILED", message="Simulated provider failure.")
            )

        query = request.message or ""
        q_lower = query.lower()
        
        if "extract" in q_lower:
            mock_content = (
                "### Tasks\n"
                "- Implement API gateway authentication\n"
                "  - Responsible: Engineering Team\n"
                "  - Deadline: Q3 Release\n\n"
                "### Decisions\n"
                "- Use FastAPI with PostgreSQL for backend architecture"
            )
        elif any(k in q_lower for k in ["summarize", "summary"]):
            mock_content = (
                "### Discussion Summary\n\n"
                "• **Architectural Overview**: The team reviewed the API gateway implementation and agreed to use JWT authentication.\n"
                "• **Pending Items**: Database schema migration and load testing are scheduled for completion next week."
            )
        elif any(k in q_lower for k in ["architecture.pdf", "api gateway"]):
            mock_content = "According to Architecture.pdf [1], the API gateway handles authentication, rate limiting, and routes requests to backend services."
        elif any(k in q_lower for k in ["architectur", "decision"]):
            mock_content = (
                "### Architectural Decisions\n\n"
                "• **Backend Framework**: Built on FastAPI with asynchronous SQLAlchemy and PostgreSQL.\n"
                "• **Security & Auth**: JWT tokens with role-based access control (RBAC).\n"
                "• **AI Pipeline**: Multi-domain retrieval augmented generation with grounded citations."
            )
        else:
            mock_content = f"Grounded response based on workspace knowledge for: '{query}'"
            
        prompt_tokens = self.count_tokens(query)
        comp_tokens = self.count_tokens(mock_content)
        total_latency = int((time.time() - start_time) * 1000)

        return AIResponse(
            request_id=request.request_id,
            conversation_id=request.conversation_id,
            content=mock_content,
            status=AIResponseStatus.COMPLETED,
            model=self.model_name,
            provider=self.provider_name,
            usage=AIUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=comp_tokens,
                total_tokens=prompt_tokens + comp_tokens,
                estimated_cost_usd=0.0
            ),
            timing=AITiming(
                request_start_time=start_time,
                completion_time=time.time(),
                total_latency_ms=total_latency,
                provider_latency_ms=total_latency
            )
        )

    async def stream_response(self, request: AIRequest) -> AsyncGenerator[AIStreamEvent, None]:
        if self.fail_mode:
            yield AIStreamEvent(
                type="ERROR",
                content="Simulated provider stream failure.",
                request_id=str(request.request_id),
                conversation_id=str(request.conversation_id) if request.conversation_id else None
            )
            return

        yield AIStreamEvent(
            type="START",
            request_id=str(request.request_id),
            conversation_id=str(request.conversation_id) if request.conversation_id else None,
            metadata={"model": self.model_name, "provider": self.provider_name}
        )

        query = request.message or ""
        q_lower = query.lower()
        if "extract" in q_lower:
            mock_content = (
                "### Tasks\n"
                "- Implement API gateway authentication\n"
                "  - Responsible: Engineering Team\n"
                "  - Deadline: Q3 Release\n\n"
                "### Decisions\n"
                "- Use FastAPI with PostgreSQL for backend architecture"
            )
        elif any(k in q_lower for k in ["summarize", "summary"]):
            mock_content = (
                "### Discussion Summary\n\n"
                "• **Architectural Overview**: The team reviewed the API gateway implementation and agreed to use JWT authentication.\n"
                "• **Pending Items**: Database schema migration and load testing are scheduled for completion next week."
            )
        elif any(k in q_lower for k in ["architecture.pdf", "api gateway"]):
            mock_content = "According to Architecture.pdf [1], the API gateway handles authentication, rate limiting, and routes requests to backend services."
        elif any(k in q_lower for k in ["architectur", "decision"]):
            mock_content = (
                "### Architectural Decisions\n\n"
                "• **Backend Framework**: Built on FastAPI with asynchronous SQLAlchemy and PostgreSQL.\n"
                "• **Security & Auth**: JWT tokens with role-based access control (RBAC).\n"
                "• **AI Pipeline**: Multi-domain retrieval augmented generation with grounded citations."
            )
        else:
            mock_content = f"Grounded response based on workspace knowledge for: '{query}'"

        words = mock_content.split(" ")
        for word in words:
            yield AIStreamEvent(
                type="TOKEN",
                content=word + " ",
                request_id=str(request.request_id),
                conversation_id=str(request.conversation_id) if request.conversation_id else None
            )
            await asyncio.sleep(0.005)

        yield AIStreamEvent(
            type="COMPLETE",
            content=mock_content,
            request_id=str(request.request_id),
            conversation_id=str(request.conversation_id) if request.conversation_id else None
        )

    # ----------------- BACKWARD COMPATIBILITY METHODS -----------------

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, settings: Optional[Any] = None) -> UnifiedLLMResponse:
        req = AIRequest(user_id=uuid.uuid4(), message=prompt, system_context=system_prompt)
        res = await self.generate_response(req)
        return UnifiedLLMResponse(
            content=res.content,
            model=res.model,
            provider=res.provider,
            prompt_tokens=res.usage.prompt_tokens,
            completion_tokens=res.usage.completion_tokens,
            total_tokens=res.usage.total_tokens,
            estimated_cost_usd=res.usage.estimated_cost_usd,
            latency_ms=res.timing.total_latency_ms
        )

    async def stream_generate(self, prompt: str, system_prompt: Optional[str] = None, settings: Optional[Any] = None) -> AsyncGenerator[str, None]:
        req = AIRequest(user_id=uuid.uuid4(), message=prompt, system_context=system_prompt)
        async for evt in self.stream_response(req):
            if evt.type == "TOKEN" and evt.content:
                yield evt.content
