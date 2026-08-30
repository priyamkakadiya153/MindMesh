import os
import random
import hashlib
import logging
import httpx
from abc import ABC, abstractmethod
from typing import List, Optional

logger = logging.getLogger(__name__)

class BaseEmbeddingProvider(ABC):
    def __init__(self, model_name: str, dimension: int):
        self.model_name = model_name
        self.dimension = dimension

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a batch of text strings."""
        pass

    async def embed_query(self, text: str) -> List[float]:
        """Generates single embedding vector for search queries."""
        res = await self.embed_texts([text])
        return res[0] if res else [0.0] * self.dimension

    def _generate_mock_vector(self, text: str) -> List[float]:
        """Generates deterministic mock float vectors when services are unavailable."""
        seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)
        vec = [rng.uniform(-1.0, 1.0) for _ in range(self.dimension)]
        # Normalize vector length
        norm = (sum(x * x for x in vec)) ** 0.5
        return [x / norm for x in vec] if norm > 0 else vec

EmbeddingProvider = BaseEmbeddingProvider


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, model_name: str = "text-embedding-004"):
        super().__init__(model_name=model_name, dimension=768)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            logger.info("Gemini API key not configured. Falling back to deterministic mock vectors.")
            return [self._generate_mock_vector(t) for t in texts]

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:batchEmbedContents?key={api_key}"
            requests_payload = [
                {
                    "model": f"models/{self.model_name}",
                    "content": {"parts": [{"text": t}]}
                }
                for t in texts
            ]
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json={"requests": requests_payload})
                if resp.status_code == 200:
                    data = resp.json()
                    embeddings = []
                    for item in data.get("embeddings", []):
                        embeddings.append(item.get("values", []))
                    if len(embeddings) == len(texts):
                        return embeddings

            logger.warning("Gemini API response invalid. Using mock vector fallback.")
            return [self._generate_mock_vector(t) for t in texts]
        except Exception as e:
            logger.error(f"Gemini embedding generation exception: {e}. Falling back to mock vectors.")
            return [self._generate_mock_vector(t) for t in texts]

class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, model_name: str = "text-embedding-3-small"):
        dim = 3072 if "large" in model_name else 1536
        super().__init__(model_name=model_name, dimension=dim)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key or api_key == "mock-key":
            logger.info("OpenAI API key missing. Falling back to deterministic mock vectors.")
            return [self._generate_mock_vector(t) for t in texts]

        try:
            import openai
            client = openai.AsyncOpenAI(api_key=api_key)
            resp = await client.embeddings.create(model=self.model_name, input=texts)
            return [item.embedding for item in resp.data]
        except Exception as e:
            logger.error(f"OpenAI embedding generation exception: {e}. Falling back to mock vectors.")
            return [self._generate_mock_vector(t) for t in texts]

class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, model_name: str = "nomic-embed-text"):
        super().__init__(model_name=model_name, dimension=768)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        url = f"{host}/api/embeddings"
        embeddings = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for text in texts:
                    resp = await client.post(url, json={"model": self.model_name, "prompt": text})
                    if resp.status_code == 200:
                        embeddings.append(resp.json().get("embedding", []))
                    else:
                        embeddings.append(self._generate_mock_vector(text))
            return embeddings
        except Exception as e:
            logger.error(f"Ollama local embedding exception: {e}. Falling back to mock vectors.")
            return [self._generate_mock_vector(t) for t in texts]

class EmbeddingProviderFactory:
    @staticmethod
    def get_provider(provider_name: str = "gemini", model_name: Optional[str] = None) -> BaseEmbeddingProvider:
        p_name = (provider_name or "gemini").lower()
        if "gemini" in p_name or "google" in p_name:
            return GeminiEmbeddingProvider(model_name=model_name or "text-embedding-004")
        elif "openai" in p_name:
            return OpenAIEmbeddingProvider(model_name=model_name or "text-embedding-3-small")
        elif "ollama" in p_name or "nomic" in p_name:
            return OllamaEmbeddingProvider(model_name=model_name or "nomic-embed-text")
        else:
            return GeminiEmbeddingProvider(model_name="text-embedding-004")
