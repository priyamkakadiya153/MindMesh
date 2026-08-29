import os
import logging
from enum import Enum
from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

class ModelCapability(str, Enum):
    TEXT_GENERATION = "text_generation"
    STREAMING = "streaming"
    VISION = "vision"
    TOOL_CALLING = "tool_calling"
    STRUCTURED_OUTPUT = "structured_output"

@dataclass
class ModelInfo:
    model_name: str
    provider: str
    capabilities: Set[ModelCapability]
    max_input_tokens: int = 128000
    max_output_tokens: int = 8192
    supports_system_instruction: bool = True
    input_cost_per_1m: float = 0.0
    output_cost_per_1m: float = 0.0

class ModelRegistry:
    """Central registry of supported AI models, providers, and capabilities."""

    _models: Dict[str, ModelInfo] = {
        "gemini-1.5-flash": ModelInfo(
            model_name="gemini-1.5-flash",
            provider="gemini",
            capabilities={
                ModelCapability.TEXT_GENERATION,
                ModelCapability.STREAMING,
                ModelCapability.STRUCTURED_OUTPUT,
            },
            max_input_tokens=1048576,
            max_output_tokens=8192,
            input_cost_per_1m=0.075,
            output_cost_per_1m=0.30,
        ),
        "gemini-2.0-flash": ModelInfo(
            model_name="gemini-2.0-flash",
            provider="gemini",
            capabilities={
                ModelCapability.TEXT_GENERATION,
                ModelCapability.STREAMING,
                ModelCapability.STRUCTURED_OUTPUT,
            },
            max_input_tokens=1048576,
            max_output_tokens=8192,
            input_cost_per_1m=0.10,
            output_cost_per_1m=0.40,
        ),
        "gemini-2.5-flash": ModelInfo(
            model_name="gemini-2.5-flash",
            provider="gemini",
            capabilities={
                ModelCapability.TEXT_GENERATION,
                ModelCapability.STREAMING,
                ModelCapability.STRUCTURED_OUTPUT,
            },
            max_input_tokens=1048576,
            max_output_tokens=8192,
            input_cost_per_1m=0.15,
            output_cost_per_1m=0.60,
        ),
        "gpt-4o-mini": ModelInfo(
            model_name="gpt-4o-mini",
            provider="openai",
            capabilities={
                ModelCapability.TEXT_GENERATION,
                ModelCapability.STREAMING,
                ModelCapability.STRUCTURED_OUTPUT,
            },
            max_input_tokens=128000,
            max_output_tokens=16384,
            input_cost_per_1m=0.15,
            output_cost_per_1m=0.60,
        ),
        "mock-model": ModelInfo(
            model_name="mock-model",
            provider="mock",
            capabilities={
                ModelCapability.TEXT_GENERATION,
                ModelCapability.STREAMING,
                ModelCapability.STRUCTURED_OUTPUT,
            },
            max_input_tokens=32000,
            max_output_tokens=4096,
            input_cost_per_1m=0.0,
            output_cost_per_1m=0.0,
        ),
    }

    @classmethod
    def register_model(cls, info: ModelInfo) -> None:
        cls._models[info.model_name] = info

    @classmethod
    def get_model(cls, model_name: str) -> Optional[ModelInfo]:
        return cls._models.get(model_name)

    @classmethod
    def list_models(cls, provider: Optional[str] = None) -> List[str]:
        if provider:
            return [m for m, info in cls._models.items() if info.provider == provider]
        return list(cls._models.keys())

    @classmethod
    def has_capability(cls, model_name: str, capability: ModelCapability) -> bool:
        info = cls.get_model(model_name)
        if not info:
            return False
        return capability in info.capabilities

@dataclass
class AIConfig:
    """Centralized AI System Configuration."""
    default_provider: str = os.getenv("DEFAULT_AI_PROVIDER", "gemini")
    default_model: str = os.getenv("DEFAULT_AI_MODEL", "gemini-1.5-flash")
    default_temperature: float = float(os.getenv("AI_TEMPERATURE", "0.2"))
    default_max_tokens: int = int(os.getenv("AI_MAX_TOKENS", "2048"))
    timeout_seconds: float = float(os.getenv("AI_REQUEST_TIMEOUT", "30.0"))
    max_message_length: int = int(os.getenv("AI_MAX_MESSAGE_LENGTH", "32000"))
    retry_max_attempts: int = int(os.getenv("AI_RETRY_MAX_ATTEMPTS", "3"))
    retry_initial_backoff_seconds: float = float(os.getenv("AI_RETRY_BACKOFF", "0.5"))
    streaming_enabled: bool = os.getenv("AI_STREAMING_ENABLED", "true").lower() == "true"
    prompt_version: str = "mindmesh-chat-v1"

    # Capability configuration
    supported_providers: List[str] = field(default_factory=lambda: ["gemini", "openai", "anthropic", "ollama", "mock"])

def validate_ai_config(config: Optional[AIConfig] = None) -> bool:
    """
    Validates AI configuration settings on application startup.
    Returns True if valid, raises ValueError if critical configuration is missing or invalid.
    """
    cfg = config or AIConfig()
    
    if not cfg.default_provider:
        raise ValueError("[AIConfig] Default AI provider is not configured.")
    
    if not cfg.default_model:
        raise ValueError("[AIConfig] Default AI model is not configured.")
    
    if cfg.default_temperature < 0.0 or cfg.default_temperature > 2.0:
        raise ValueError(f"[AIConfig] Invalid temperature {cfg.default_temperature}. Must be between 0.0 and 2.0.")
    
    if cfg.timeout_seconds <= 0:
        raise ValueError(f"[AIConfig] Invalid timeout {cfg.timeout_seconds}. Must be > 0.")
    
    if cfg.max_message_length <= 0:
        raise ValueError(f"[AIConfig] Invalid max_message_length {cfg.max_message_length}. Must be > 0.")

    logger.info(f"[AIConfig Validation OK] Provider: {cfg.default_provider}, Model: {cfg.default_model}, Timeout: {cfg.timeout_seconds}s")
    return True

ai_config = AIConfig()
