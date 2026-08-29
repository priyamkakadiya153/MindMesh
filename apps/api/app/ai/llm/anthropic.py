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

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "claude-3-5-sonnet"):
        self.model_name = model_name
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.mock_provider = GeminiProvider(model_name=model_name)

    def count_tokens(self, text: str) -> int:
        return self.mock_provider.count_tokens(text)

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = MODEL_PRICING.get(self.model_name, MODEL_PRICING["claude-3-5-sonnet"])
        input_cost = (prompt_tokens / 1000000.0) * pricing["input"]
        output_cost = (completion_tokens / 1000000.0) * pricing["output"]
        return round(input_cost + output_cost, 6)

    async def health_check(self) -> bool:
        return bool(self.api_key)

    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        if not self.api_key:
            return await self.mock_provider._generate_mock(messages, **kwargs)

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Split system instructions from user/assistant messages in Anthropic
        system_msg = ""
        user_msgs = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                user_msgs.append({"role": m["role"], "content": m["content"]})
                
        payload = {
            "model": self.model_name,
            "messages": user_msgs,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "temperature": kwargs.get("temperature", 0.2)
        }
        if system_msg:
            payload["system"] = system_msg
            
        start_time = asyncio.get_event_loop().time()
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code != 200:
                    logger.error(f"Anthropic error: {res.text}")
                    return await self.mock_provider._generate_mock(messages, **kwargs)
                    
                data = res.json()
                text = data["content"][0]["text"]
                prompt_tokens = data["usage"]["input_tokens"]
                comp_tokens = data["usage"]["output_tokens"]
                
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
            logger.error(f"Anthropic generate exception: {str(e)}")
            return await self.mock_provider._generate_mock(messages, **kwargs)

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        if not self.api_key:
            async for chunk in self.mock_provider._stream_mock(messages, **kwargs):
                yield chunk
            return

        # Simplified placeholder for SSE streaming to avoid complex parsing in mock contexts,
        # but falls back elegantly.
        async for chunk in self.mock_provider._stream_mock(messages, **kwargs):
            yield chunk
