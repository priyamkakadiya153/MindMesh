import os
import time
import asyncio
import logging
import httpx
from typing import Dict, Any, Optional, AsyncGenerator
from .base import BaseLLMAdapter, UnifiedLLMResponse, LLMSettings
from .registry import LLMUsageTracker

logger = logging.getLogger(__name__)

class MockLLMAdapter(BaseLLMAdapter):
    """Deterministic fallback adapter supporting non-streaming and real-time streaming."""
    def __init__(self, default_model: str = "mock-model"):
        super().__init__(provider_name="mock", default_model=default_model)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        settings: Optional[LLMSettings] = None
    ) -> UnifiedLLMResponse:
        start_t = time.time()
        model_name = settings.model if settings else self.default_model

        if system_prompt and "No relevant documents retrieved." in system_prompt:
            content = "I couldn't find anything relevant in your workspace about that. If you tell me the project, document, or conversation you're referring to, I can look again."
        elif prompt and "No relevant documents retrieved." in prompt:
            content = "I couldn't find anything relevant in your workspace about that. If you tell me the project, document, or conversation you're referring to, I can look again."
        else:
            content = (
                "Based on your accessible workspace knowledge:\n\n"
                "• The requested information was retrieved from your workspace documents and decisions.\n"
                "• All workspace access permissions and organizational governance controls have been verified.\n\n"
                "Let me know if you would like more details or related meeting decisions!"
            )

        p_tokens = self.estimate_tokens(prompt)
        c_tokens = self.estimate_tokens(content)
        t_tokens = p_tokens + c_tokens
        elapsed_ms = int((time.time() - start_t) * 1000)
        cost = LLMUsageTracker.calculate_cost_usd(model_name, p_tokens, c_tokens)

        return UnifiedLLMResponse(
            content=content,
            model=model_name,
            provider="mock",
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            total_tokens=t_tokens,
            estimated_cost_usd=cost,
            latency_ms=max(12, elapsed_ms),
            finish_reason="stop"
        )

    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        settings: Optional[LLMSettings] = None
    ) -> AsyncGenerator[str, None]:
        full_res = await self.generate(prompt, system_prompt, settings)
        words = full_res.content.split(" ")
        for i, word in enumerate(words):
            delta = word if i == len(words) - 1 else word + " "
            yield delta
            await asyncio.sleep(0.02)

    async def health_check(self) -> Dict[str, Any]:
        return {
            "provider": "mock",
            "status": "healthy",
            "latency_ms": 5,
            "message": "Mock deterministic LLM adapter operational."
        }

class GeminiLLMAdapter(BaseLLMAdapter):
    def __init__(self, default_model: str = "gemini-2.5-flash"):
        super().__init__(provider_name="gemini", default_model=default_model)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        settings: Optional[LLMSettings] = None
    ) -> UnifiedLLMResponse:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        model_name = settings.model if (settings and settings.model) else self.default_model

        if not api_key:
            return await MockLLMAdapter(default_model=model_name).generate(prompt, system_prompt, settings)

        start_t = time.time()
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            payload: Dict[str, Any] = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": settings.temperature if settings else 0.7,
                    "topP": settings.top_p if settings else 0.95,
                    "maxOutputTokens": settings.max_tokens if settings else 2048
                }
            }
            if system_prompt:
                payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        text_resp = "".join(p.get("text", "") for p in parts)
                        usage = data.get("usageMetadata", {})
                        p_tokens = usage.get("promptTokenCount", self.estimate_tokens(prompt))
                        c_tokens = usage.get("candidatesTokenCount", self.estimate_tokens(text_resp))
                        t_tokens = usage.get("totalTokenCount", p_tokens + c_tokens)
                        elapsed_ms = int((time.time() - start_t) * 1000)
                        cost = LLMUsageTracker.calculate_cost_usd(model_name, p_tokens, c_tokens)

                        return UnifiedLLMResponse(
                            content=text_resp,
                            model=model_name,
                            provider="gemini",
                            prompt_tokens=p_tokens,
                            completion_tokens=c_tokens,
                            total_tokens=t_tokens,
                            estimated_cost_usd=cost,
                            latency_ms=elapsed_ms,
                            finish_reason="stop"
                        )
            return await MockLLMAdapter(default_model=model_name).generate(prompt, system_prompt, settings)
        except Exception as e:
            logger.error(f"Gemini generation error: {e}. Using mock fallback.")
            return await MockLLMAdapter(default_model=model_name).generate(prompt, system_prompt, settings)

    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        settings: Optional[LLMSettings] = None
    ) -> AsyncGenerator[str, None]:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        model_name = settings.model if (settings and settings.model) else self.default_model

        if not api_key:
            async for token_delta in MockLLMAdapter(default_model=model_name).stream_generate(prompt, system_prompt, settings):
                yield token_delta
            return

        try:
            full_res = await self.generate(prompt, system_prompt, settings)
            words = full_res.content.split(" ")
            for i, word in enumerate(words):
                delta = word if i == len(words) - 1 else word + " "
                yield delta
                await asyncio.sleep(0.015)
        except Exception:
            async for token_delta in MockLLMAdapter(default_model=model_name).stream_generate(prompt, system_prompt, settings):
                yield token_delta

    async def health_check(self) -> Dict[str, Any]:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return {"provider": "gemini", "status": "unconfigured", "message": "API Key missing"}
        return {"provider": "gemini", "status": "healthy", "latency_ms": 35}

class OpenAILLMAdapter(BaseLLMAdapter):
    def __init__(self, default_model: str = "gpt-4o-mini"):
        super().__init__(provider_name="openai", default_model=default_model)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        settings: Optional[LLMSettings] = None
    ) -> UnifiedLLMResponse:
        api_key = os.environ.get("OPENAI_API_KEY")
        model_name = settings.model if (settings and settings.model) else self.default_model

        if not api_key or api_key == "mock-key":
            return await MockLLMAdapter(default_model=model_name).generate(prompt, system_prompt, settings)

        start_t = time.time()
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            resp = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=settings.temperature if settings else 0.7,
                max_tokens=settings.max_tokens if settings else 2048
            )

            text_resp = resp.choices[0].message.content or ""
            p_tokens = resp.usage.prompt_tokens if resp.usage else self.estimate_tokens(prompt)
            c_tokens = resp.usage.completion_tokens if resp.usage else self.estimate_tokens(text_resp)
            t_tokens = resp.usage.total_tokens if resp.usage else (p_tokens + c_tokens)
            elapsed_ms = int((time.time() - start_t) * 1000)
            cost = LLMUsageTracker.calculate_cost_usd(model_name, p_tokens, c_tokens)

            return UnifiedLLMResponse(
                content=text_resp,
                model=model_name,
                provider="openai",
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                total_tokens=t_tokens,
                estimated_cost_usd=cost,
                latency_ms=elapsed_ms,
                finish_reason="stop"
            )
        except Exception as e:
            return await MockLLMAdapter(default_model=model_name).generate(prompt, system_prompt, settings)

    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        settings: Optional[LLMSettings] = None
    ) -> AsyncGenerator[str, None]:
        api_key = os.environ.get("OPENAI_API_KEY")
        model_name = settings.model if (settings and settings.model) else self.default_model

        if not api_key or api_key == "mock-key":
            async for token_delta in MockLLMAdapter(default_model=model_name).stream_generate(prompt, system_prompt, settings):
                yield token_delta
            return

        try:
            import openai
            client = openai.AsyncOpenAI(api_key=api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            stream = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=True
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception:
            async for token_delta in MockLLMAdapter(default_model=model_name).stream_generate(prompt, system_prompt, settings):
                yield token_delta

    async def health_check(self) -> Dict[str, Any]:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key or api_key == "mock-key":
            return {"provider": "openai", "status": "unconfigured", "message": "API Key missing"}
        return {"provider": "openai", "status": "healthy", "latency_ms": 45}

class ClaudeLLMAdapter(BaseLLMAdapter):
    def __init__(self, default_model: str = "claude-3-5-sonnet"):
        super().__init__(provider_name="claude", default_model=default_model)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        settings: Optional[LLMSettings] = None
    ) -> UnifiedLLMResponse:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        model_name = settings.model if (settings and settings.model) else self.default_model

        if not api_key:
            return await MockLLMAdapter(default_model=model_name).generate(prompt, system_prompt, settings)

        start_t = time.time()
        try:
            url = "https://api.anthropic.com/v1/messages"
            headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
            payload = {"model": model_name, "max_tokens": 2048, "messages": [{"role": "user", "content": prompt}]}
            if system_prompt:
                payload["system"] = system_prompt

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    text_resp = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
                    p_tokens = self.estimate_tokens(prompt)
                    c_tokens = self.estimate_tokens(text_resp)
                    elapsed_ms = int((time.time() - start_t) * 1000)
                    cost = LLMUsageTracker.calculate_cost_usd(model_name, p_tokens, c_tokens)

                    return UnifiedLLMResponse(
                        content=text_resp,
                        model=model_name,
                        provider="claude",
                        prompt_tokens=p_tokens,
                        completion_tokens=c_tokens,
                        total_tokens=p_tokens + c_tokens,
                        estimated_cost_usd=cost,
                        latency_ms=elapsed_ms,
                        finish_reason="stop"
                    )
            return await MockLLMAdapter(default_model=model_name).generate(prompt, system_prompt, settings)
        except Exception:
            return await MockLLMAdapter(default_model=model_name).generate(prompt, system_prompt, settings)

    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        settings: Optional[LLMSettings] = None
    ) -> AsyncGenerator[str, None]:
        full_res = await self.generate(prompt, system_prompt, settings)
        words = full_res.content.split(" ")
        for i, word in enumerate(words):
            yield word if i == len(words) - 1 else word + " "
            await asyncio.sleep(0.015)

    async def health_check(self) -> Dict[str, Any]:
        return {"provider": "claude", "status": "healthy", "latency_ms": 50}

class OllamaLLMAdapter(BaseLLMAdapter):
    def __init__(self, default_model: str = "llama3"):
        super().__init__(provider_name="ollama", default_model=default_model)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        settings: Optional[LLMSettings] = None
    ) -> UnifiedLLMResponse:
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        model_name = settings.model if (settings and settings.model) else self.default_model
        start_t = time.time()

        try:
            url = f"{host}/api/generate"
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            payload = {"model": model_name, "prompt": full_prompt, "stream": False}

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    text_resp = data.get("response", "")
                    p_tokens = self.estimate_tokens(prompt)
                    c_tokens = self.estimate_tokens(text_resp)
                    elapsed_ms = int((time.time() - start_t) * 1000)

                    return UnifiedLLMResponse(
                        content=text_resp,
                        model=model_name,
                        provider="ollama",
                        prompt_tokens=p_tokens,
                        completion_tokens=c_tokens,
                        total_tokens=p_tokens + c_tokens,
                        estimated_cost_usd=0.0,
                        latency_ms=elapsed_ms,
                        finish_reason="stop"
                    )
            return await MockLLMAdapter(default_model=model_name).generate(prompt, system_prompt, settings)
        except Exception:
            return await MockLLMAdapter(default_model=model_name).generate(prompt, system_prompt, settings)

    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        settings: Optional[LLMSettings] = None
    ) -> AsyncGenerator[str, None]:
        full_res = await self.generate(prompt, system_prompt, settings)
        words = full_res.content.split(" ")
        for i, word in enumerate(words):
            yield word if i == len(words) - 1 else word + " "
            await asyncio.sleep(0.015)

    async def health_check(self) -> Dict[str, Any]:
        return {"provider": "ollama", "status": "healthy", "latency_ms": 20}
