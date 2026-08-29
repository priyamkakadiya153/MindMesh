import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class LLMModelRegistry:
    """Pre-configured registry of supported cloud and local models with token pricing."""
    MODELS = {
        # Google Gemini Models
        "gemini-2.5-flash": {
            "provider": "gemini",
            "name": "Gemini 2.5 Flash",
            "context_window": 1000000,
            "prompt_cost_per_1k": 0.000075,
            "completion_cost_per_1k": 0.000300,
            "supports_system": True
        },
        "gemini-2.5-pro": {
            "provider": "gemini",
            "name": "Gemini 2.5 Pro",
            "context_window": 2000000,
            "prompt_cost_per_1k": 0.001250,
            "completion_cost_per_1k": 0.005000,
            "supports_system": True
        },
        "gemini-1.5-flash": {
            "provider": "gemini",
            "name": "Gemini 1.5 Flash",
            "context_window": 1000000,
            "prompt_cost_per_1k": 0.000075,
            "completion_cost_per_1k": 0.000300,
            "supports_system": True
        },
        # OpenAI Models
        "gpt-4o-mini": {
            "provider": "openai",
            "name": "GPT-4o Mini",
            "context_window": 128000,
            "prompt_cost_per_1k": 0.000150,
            "completion_cost_per_1k": 0.000600,
            "supports_system": True
        },
        "gpt-4o": {
            "provider": "openai",
            "name": "GPT-4o",
            "context_window": 128000,
            "prompt_cost_per_1k": 0.002500,
            "completion_cost_per_1k": 0.010000,
            "supports_system": True
        },
        "gpt-4.1": {
            "provider": "openai",
            "name": "GPT-4.1 Turbo",
            "context_window": 128000,
            "prompt_cost_per_1k": 0.003000,
            "completion_cost_per_1k": 0.012000,
            "supports_system": True
        },
        # Anthropic Claude Models
        "claude-3-5-sonnet": {
            "provider": "claude",
            "name": "Claude 3.5 Sonnet",
            "context_window": 200000,
            "prompt_cost_per_1k": 0.003000,
            "completion_cost_per_1k": 0.015000,
            "supports_system": True
        },
        # Local Ollama Models
        "llama3": {
            "provider": "ollama",
            "name": "Llama 3 (8B Local)",
            "context_window": 8192,
            "prompt_cost_per_1k": 0.0,
            "completion_cost_per_1k": 0.0,
            "supports_system": True
        },
        "mistral": {
            "provider": "ollama",
            "name": "Mistral (7B Local)",
            "context_window": 8192,
            "prompt_cost_per_1k": 0.0,
            "completion_cost_per_1k": 0.0,
            "supports_system": True
        }
    }

    @classmethod
    def get_model_info(cls, model_id: str) -> Dict[str, Any]:
        return cls.MODELS.get(model_id, {
            "provider": "unknown",
            "name": model_id,
            "context_window": 128000,
            "prompt_cost_per_1k": 0.0001,
            "completion_cost_per_1k": 0.0003,
            "supports_system": True
        })

    @classmethod
    def list_all_models(cls) -> List[Dict[str, Any]]:
        return [{"id": k, **v} for k, v in cls.MODELS.items()]

class LLMUsageTracker:
    """Calculates USD cost and tracks token consumption metrics."""
    @staticmethod
    def calculate_cost_usd(model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
        info = LLMModelRegistry.get_model_info(model_id)
        p_cost = (prompt_tokens / 1000.0) * info.get("prompt_cost_per_1k", 0.0)
        c_cost = (completion_tokens / 1000.0) * info.get("completion_cost_per_1k", 0.0)
        return round(p_cost + c_cost, 6)
