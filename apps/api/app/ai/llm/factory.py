import logging
from typing import Optional, Dict, Any, List
from app.ai.llm.base import ModelProvider, UnifiedLLMResponse, LLMSettings
from app.ai.llm.gemini import GeminiProvider
from app.ai.llm.mock import MockModelProvider

logger = logging.getLogger(__name__)

class LLMProviderFactory:
    """Factory creating interchangeable ModelProvider adapters and managing provider resolution."""

    _registry: Dict[str, type] = {
        "gemini": GeminiProvider,
        "google": GeminiProvider,
        "mock": MockModelProvider,
    }

    @classmethod
    def register_provider(cls, name: str, provider_cls: type) -> None:
        cls._registry[name.lower()] = provider_cls

    @classmethod
    def list_supported_providers(cls) -> List[str]:
        return sorted(list(set(cls._registry.keys())))

    @classmethod
    def get_provider(cls, provider_name: str = "gemini", model_name: Optional[str] = None) -> ModelProvider:
        p_name = (provider_name or "gemini").lower().strip()
        
        if p_name in cls._registry:
            provider_cls = cls._registry[p_name]
            return provider_cls(model_name=model_name or "gemini-1.5-flash")
        
        if "gemini" in p_name or "google" in p_name:
            return GeminiProvider(model_name=model_name or "gemini-1.5-flash")
        elif "mock" in p_name:
            return MockModelProvider(model_name=model_name or "mock-model")
        else:
            # Import dynamically from adapters if present, or fallback to MockModelProvider
            try:
                from .adapters import GeminiLLMAdapter, OpenAILLMAdapter, ClaudeLLMAdapter, OllamaLLMAdapter
                if "openai" in p_name:
                    return OpenAILLMAdapter(default_model=model_name or "gpt-4o-mini")
                elif "claude" in p_name or "anthropic" in p_name:
                    return ClaudeLLMAdapter(default_model=model_name or "claude-3-5-sonnet")
                elif "ollama" in p_name:
                    return OllamaLLMAdapter(default_model=model_name or "llama3")
            except Exception as e:
                logger.warning(f"Could not load dynamic adapter for '{p_name}': {e}")

            logger.info(f"Unrecognized provider '{p_name}'. Falling back to MockModelProvider.")
            return MockModelProvider(model_name=model_name or "mock-model")

    @classmethod
    async def generate_with_failover(
        cls,
        prompt: str,
        system_prompt: Optional[str] = None,
        settings: Optional[LLMSettings] = None
    ) -> UnifiedLLMResponse:
        """Executes LLM generation with automatic retry & fallback provider failover."""
        cfg = settings or LLMSettings()
        primary_name = cfg.provider
        fallback_name = cfg.fallback_provider

        primary_adapter = cls.get_provider(primary_name, cfg.model)

        for attempt in range(1, 3):
            try:
                if hasattr(primary_adapter, "generate"):
                    res = await primary_adapter.generate(prompt, system_prompt, cfg)
                    if res and getattr(res, "content", None):
                        return res
            except Exception as err:
                logger.warning(f"Primary provider '{primary_name}' attempt {attempt} failed: {err}")

        logger.info(f"Failing over to secondary provider '{fallback_name}'.")
        try:
            fallback_adapter = cls.get_provider(fallback_name, cfg.fallback_model)
            if hasattr(fallback_adapter, "generate"):
                res = await fallback_adapter.generate(prompt, system_prompt, cfg)
                if res and getattr(res, "content", None):
                    return res
        except Exception as err:
            logger.error(f"Fallback provider '{fallback_name}' failed: {err}")

        mock_adapter = MockModelProvider(model_name=cfg.model)
        req_res = await mock_adapter.generate_response(
            AIRequest(user_id=None, message=prompt, system_context=system_prompt)
        )
        return UnifiedLLMResponse(
            content=req_res.content,
            model=req_res.model,
            provider=req_res.provider,
            prompt_tokens=req_res.usage.prompt_tokens,
            completion_tokens=req_res.usage.completion_tokens,
            total_tokens=req_res.usage.total_tokens,
            estimated_cost_usd=req_res.usage.estimated_cost_usd,
            latency_ms=req_res.timing.total_latency_ms
        )
