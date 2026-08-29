import os
import logging
import asyncio
import httpx
from typing import List, Dict, Any, AsyncGenerator
from .base import BaseLLMProvider
from .pricing import MODEL_PRICING
from .gemini import GeminiProvider # Reuse mock generators

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.mock_provider = GeminiProvider(model_name=model_name)

    def count_tokens(self, text: str) -> int:
        return self.mock_provider.count_tokens(text)

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = MODEL_PRICING.get(self.model_name, MODEL_PRICING["gpt-4o"])
        input_cost = (prompt_tokens / 1000000.0) * pricing["input"]
        output_cost = (completion_tokens / 1000000.0) * pricing["output"]
        return round(input_cost + output_cost, 6)

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                return res.status_code == 200
        except Exception:
            return False

    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        if not self.api_key:
            return await self.mock_provider._generate_mock(messages, **kwargs)

        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.2)
        }
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]
            
        start_time = asyncio.get_event_loop().time()
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    url,
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                if res.status_code != 200:
                    logger.error(f"OpenAI error: {res.text}")
                    return await self.mock_provider._generate_mock(messages, **kwargs)
                    
                data = res.json()
                text = data["choices"][0]["message"]["content"]
                prompt_tokens = data["usage"]["prompt_tokens"]
                comp_tokens = data["usage"]["completion_tokens"]
                
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
            logger.error(f"OpenAI generate exception: {str(e)}")
            return await self.mock_provider._generate_mock(messages, **kwargs)

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        if not self.api_key:
            async for chunk in self.mock_provider._stream_mock(messages, **kwargs):
                yield chunk
            return

        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.2),
            "stream": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST",
                    url,
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                ) as response:
                    if response.status_code != 200:
                        async for chunk in self.mock_provider._stream_mock(messages, **kwargs):
                            yield chunk
                        return

                    async for line in response.iter_lines():
                        if not line or not line.strip():
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk_json = json.loads(data_str)
                                delta = chunk_json["choices"][0]["delta"]
                                if "content" in delta:
                                    yield delta["content"]
                            except Exception:
                                pass
        except Exception as e:
            logger.error(f"OpenAI stream exception: {str(e)}")
            async for chunk in self.mock_provider._stream_mock(messages, **kwargs):
                yield chunk
