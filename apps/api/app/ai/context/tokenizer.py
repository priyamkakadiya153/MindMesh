import logging
from typing import Dict, Any
from app.ai.chunking.statistics import TokenCounter

logger = logging.getLogger(__name__)

# Standard model token budget configurations
MODEL_BUDGETS: Dict[str, Dict[str, int]] = {
    "gemini-2.0-flash": {
        "total": 1048576,      # 1M context
        "system": 4000,
        "history": 200000,
        "context": 700000,
        "query": 10000,
        "response": 8192
    },
    "gpt-4": {
        "total": 8192,
        "system": 500,
        "history": 1500,
        "context": 3000,
        "query": 500,
        "response": 2000
    },
    "gpt-3.5-turbo": {
        "total": 4096,
        "system": 300,
        "history": 1000,
        "context": 1500,
        "query": 300,
        "response": 1000
    },
    "default": {
        "total": 10000,
        "system": 500,
        "history": 1500,
        "context": 5000,
        "query": 500,
        "response": 2500
    }
}

class TokenBudgetManager:
    @staticmethod
    def count_tokens(text: str) -> int:
        """Counts or estimates the token count of a given string."""
        try:
            # Fall back to checking if tiktoken can be dynamically imported
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text or ""))
        except Exception:
            return TokenCounter.count_tokens(text)

    @classmethod
    def get_model_budget(cls, model_name: str) -> Dict[str, int]:
        """Retrieves token allocation dictionary for a specific model."""
        normalized_name = (model_name or "default").lower()
        for key in MODEL_BUDGETS:
            if key in normalized_name:
                return MODEL_BUDGETS[key]
        return MODEL_BUDGETS["default"]

    @classmethod
    def allocate_budget(cls, model_name: str, query: str, history_text: str = "") -> Dict[str, int]:
        """Allocates token budgets dynamically based on inputs."""
        budget = cls.get_model_budget(model_name)
        query_tokens = cls.count_tokens(query)
        history_tokens = cls.count_tokens(history_text)
        
        # Adjust dynamic slots
        allocated_query = min(query_tokens, budget["query"])
        allocated_history = min(history_tokens, budget["history"])
        
        # Context takes the rest of the available input capacity
        max_context = budget["total"] - (budget["system"] + budget["response"] + allocated_query + allocated_history)
        max_context = max(0, min(max_context, budget["context"]))
        
        return {
            "total_limit": budget["total"],
            "system_limit": budget["system"],
            "query_limit": budget["query"],
            "query_actual": allocated_query,
            "history_limit": budget["history"],
            "history_actual": allocated_history,
            "context_limit": max_context,
            "response_limit": budget["response"]
        }
