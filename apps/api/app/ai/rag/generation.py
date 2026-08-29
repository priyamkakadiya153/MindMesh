import logging
from typing import List, Dict, Any, AsyncGenerator
from ..llm.factory import LLMProviderFactory

logger = logging.getLogger(__name__)

class RAGGeneration:
    @staticmethod
    async def generate_response(
        messages: List[Dict[str, str]],
        provider_name: str = "gemini",
        model_name: str = "gemini-2.0-flash",
        **kwargs
    ) -> Dict[str, Any]:
        """Calls active LLM factory to generate static response."""
        provider = LLMProviderFactory.get_provider(provider_name, model_name)
        return await provider.generate(messages, **kwargs)

    @staticmethod
    async def stream_response(
        messages: List[Dict[str, str]],
        provider_name: str = "gemini",
        model_name: str = "gemini-2.0-flash",
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Calls active LLM factory to stream response tokens."""
        provider = LLMProviderFactory.get_provider(provider_name, model_name)
        async for token in provider.stream(messages, **kwargs):
            yield token
