import logging
import asyncio
import httpx
import json
from typing import List, Dict, Any, AsyncGenerator
from .base import BaseLLMProvider
from .gemini import GeminiProvider

logger = logging.getLogger(__name__)

class LMStudioProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "local-model", base_url: str = "http://localhost:1234/v1"):
        self.model_name = model_name
        self.base_url = base_url
        self.fallback_provider = GeminiProvider(model_name=model_name)

    def count_tokens(self, text: str) -> int:
        return self.fallback_provider.count_tokens(text)

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return 0.0 # LM Studio local is free!

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/models")
                return res.status_code == 200
        except Exception:
            return False

    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "temperature": kwargs.get("temperature", 0.2),
            "max_tokens": kwargs.get("max_tokens", 1024)
        }
        
        start_time = asyncio.get_event_loop().time()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code != 200:
                    return await self.fallback_provider._generate_mock(messages, **kwargs)
                    
                data = res.json()
                text = data["choices"][0]["message"]["content"]
                
                prompt_tokens = data.get("usage", {}).get("prompt_tokens") or self.count_tokens(" ".join(m["content"] for m in messages))
                comp_tokens = data.get("usage", {}).get("completion_tokens") or self.count_tokens(text)
                latency_ms = int((asyncio.get_event_loop().time() - start_time) * 1000.0)
                
                return {
                    "text": text,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": comp_tokens,
                    "cost": 0.0,
                    "latency_ms": latency_ms,
                    "model": self.model_name
                }
        except Exception as e:
            logger.warning(f"LM Studio provider exception: {e}. Falling back to default generator.")
            return await self.fallback_provider._generate_mock(messages, **kwargs)

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
            "temperature": kwargs.get("temperature", 0.2),
            "max_tokens": kwargs.get("max_tokens", 1024)
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        async for chunk in self.fallback_provider._stream_mock(messages, **kwargs):
                            yield chunk
                        return

                    async for line in response.iter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {}).get("content", "")
                            if delta:
                                yield delta
                        except Exception:
                            pass
        except Exception as e:
            logger.warning(f"LM Studio streaming exception: {e}. Falling back.")
            async for chunk in self.fallback_provider._stream_mock(messages, **kwargs):
                yield chunk
