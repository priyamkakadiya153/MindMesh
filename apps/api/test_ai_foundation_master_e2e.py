import uuid
import pytest
import asyncio
import time
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.config import AIConfig, ModelRegistry, ModelCapability, validate_ai_config
from app.ai.gateway.models import (
    AIRequest,
    AIResponse,
    AIResponseStatus,
    AIUsage,
    AITiming,
    AIStreamEvent,
    AIError
)
from app.ai.gateway.gateway import AIGateway
from app.ai.gateway.service import AIService
from app.ai.llm.base import ModelProvider
from app.ai.llm.mock import MockModelProvider
from app.ai.llm.gemini import GeminiProvider
from app.ai.llm.factory import LLMProviderFactory
from app.ai.prompt.builder import PromptBuilder, normalize_user_message, PROMPT_VERSION

@pytest.mark.asyncio
async def test_ai_config_validation():
    """Test AI Configuration validation and model registry capabilities."""
    cfg = AIConfig()
    assert validate_ai_config(cfg) is True
    
    assert ModelRegistry.has_capability("gemini-2.0-flash", ModelCapability.TEXT_GENERATION) is True
    assert ModelRegistry.has_capability("gemini-2.0-flash", ModelCapability.STREAMING) is True
    assert "gemini-2.0-flash" in ModelRegistry.list_models(provider="gemini")

    # Invalid config checks
    invalid_cfg = AIConfig(default_provider="")
    with pytest.raises(ValueError, match="Default AI provider is not configured"):
        validate_ai_config(invalid_cfg)

@pytest.mark.asyncio
async def test_prompt_builder_normalization_and_version():
    """Test PromptBuilder normalization rules and version tracking."""
    # 1. Normalization
    assert normalize_user_message("   hello world   ") == "hello world"
    
    with pytest.raises(ValueError, match="User message cannot be empty"):
        normalize_user_message("    ")

    with pytest.raises(ValueError, match="exceeds maximum allowed limit"):
        normalize_user_message("a" * 35000, max_length=32000)

    # 2. Prompt Versioning
    prompt_res = PromptBuilder.build_prompt(query="What is MindMesh?")
    assert prompt_res["prompt_version"] == PROMPT_VERSION
    assert prompt_res["user_query"] == "What is MindMesh?"
    assert "=== SYSTEM INSTRUCTIONS ===" in prompt_res["prompt"]

@pytest.mark.asyncio
async def test_mock_model_provider_execution():
    """Test MockModelProvider deterministic response generation and streaming."""
    provider = MockModelProvider(model_name="mock-model")
    health = await provider.health_check()
    assert health["status"] == "healthy"

    user_id = uuid.uuid4()
    req = AIRequest(
        user_id=user_id,
        message="Test query for mock provider",
        system_context="You are a test assistant."
    )

    response = await provider.generate_response(req)
    assert response.status == AIResponseStatus.COMPLETED
    assert response.provider == "mock"
    assert "Mock response for request" in response.content
    assert response.usage.prompt_tokens > 0
    assert response.timing.total_latency_ms >= 0

    # Test Streaming
    events = []
    async for evt in provider.stream_response(req):
        events.append(evt)

    assert len(events) > 2
    assert events[0].type == "START"
    assert events[-1].type == "COMPLETE"

@pytest.mark.asyncio
async def test_ai_gateway_execution_with_mock_provider():
    """Test AIGateway request execution using MockModelProvider (Provider Mock Test)."""
    gateway = AIGateway(db=None)
    user_id = uuid.uuid4()
    conv_id = uuid.uuid4()

    req = AIRequest(
        user_id=user_id,
        conversation_id=conv_id,
        message="  Explain organizational knowledge graph  ",
        model_preferences={"provider": "mock", "model": "mock-model"}
    )

    response = await gateway.execute(req)
    assert response.status == AIResponseStatus.COMPLETED
    assert response.request_id == req.request_id
    assert response.conversation_id == conv_id
    assert response.provider == "mock"
    assert "Explain organizational knowledge graph" in response.content
    assert response.metadata.get("prompt_version") == PROMPT_VERSION

@pytest.mark.asyncio
async def test_ai_gateway_empty_message_validation():
    """Test AIGateway rejects empty messages cleanly without model invocation."""
    gateway = AIGateway(db=None)
    user_id = uuid.uuid4()

    req = AIRequest(
        user_id=user_id,
        message="     ",
        model_preferences={"provider": "mock"}
    )

    response = await gateway.execute(req)
    assert response.status == AIResponseStatus.FAILED
    assert response.error is not None
    assert response.error.code == "INVALID_REQUEST"
    assert "cannot be empty" in response.error.message

@pytest.mark.asyncio
async def test_gemini_provider_adapter_fallback():
    """Test GeminiProvider adapter handling and offline fallback when API key is missing or offline."""
    provider = GeminiProvider(model_name="gemini-2.5-flash")
    user_id = uuid.uuid4()
    req = AIRequest(
        user_id=user_id,
        message="Hello Gemini",
        model_preferences={"provider": "gemini", "model": "gemini-2.5-flash"}
    )

    response = await provider.generate_response(req)
    assert response.provider == "gemini"
    assert response.status == AIResponseStatus.COMPLETED
    assert len(response.content) > 0

@pytest.mark.asyncio
async def test_provider_factory_resolution():
    """Test LLMProviderFactory provider lookup and fallback resolution."""
    gemini_p = LLMProviderFactory.get_provider("gemini")
    assert isinstance(gemini_p, GeminiProvider)

    mock_p = LLMProviderFactory.get_provider("mock")
    assert isinstance(mock_p, MockModelProvider)

    unrec_p = LLMProviderFactory.get_provider("unrecognized_provider_xyz")
    assert isinstance(unrec_p, MockModelProvider)
