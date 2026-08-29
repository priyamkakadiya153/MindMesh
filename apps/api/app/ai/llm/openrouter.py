import os
import json
import logging
import asyncio
import httpx
from typing import List, Dict, Any, AsyncGenerator
from .base import BaseLLMProvider
from .pricing import MODEL_PRICING
from .gemini import GeminiProvider

logger = logging.getLogger(__name__)

class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "meta-llama/llama-3-8b-instruct:free"):
        self.model_name = model_name
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        self.mock_provider = GeminiProvider(model_name=model_name)

    def count_tokens(self, text: str) -> int:
        return self.mock_provider.count_tokens(text)

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        # Check standard pricing or assume very low pricing
        pricing = MODEL_PRICING.get(self.model_name, {"input": 0.5, "output": 1.5})
        input_cost = (prompt_tokens / 1000000.0) * pricing["input"]
        output_cost = (completion_tokens / 1000000.0) * pricing["output"]
        return round(input_cost + output_cost, 6)

    async def health_check(self) -> bool:
        return bool(self.api_key)

    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        if not self.api_key:
            return await self.mock_provider._generate_mock(messages, **kwargs)

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://mindmesh.ai", # Site Name
            "X-Title": "MindMesh",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.2)
        }
        
        start_time = asyncio.get_event_loop().time()
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code != 200:
                    logger.error(f"OpenRouter error: {res.text}")
                    return await self.mock_provider._generate_mock(messages, **kwargs)
                    
                data = res.json()
                text = data["choices"][0]["message"]["content"]
                prompt_tokens = data.get("usage", {}).get("prompt_tokens", self.count_tokens(" ".join(m["content"] for m in messages)))
                comp_tokens = data.get("usage", {}).get("completion_tokens", self.count_tokens(text))
                
                latency_ms = int((asyncio.get_event_loop().time() - start_time) * 1000.0)
                return {
                    "text": text,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": comp_tokens,
                    "cost": self.estimate_cost(prompt_tokens, comp_tokens),
                    "latency_ms": latency_ms,
                    "model": self.model_name
                }
        except Exception as e:
            logger.error(f"OpenRouter generate exception: {str(e)}")
            return await self.mock_provider._generate_mock(messages, **kwargs)

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        if not self.api_key:
            async for chunk in self.mock_provider._stream_mock(messages, **kwargs):
                yield chunk
            return

        async for chunk in self.mock_provider._stream_mock(messages, **kwargs):
            yield chunk
