from typing import Dict, Any

# Dynamic LLM cost estimations per 1K tokens
LLM_PRICING: Dict[str, Dict[str, float]] = {
    "gemini-2.0-flash": {
        "input": 0.00015,  # $0.15 per 1M input tokens
        "output": 0.0006   # $0.60 per 1M output tokens
    },
    "gpt-4": {
        "input": 0.03,     # $30.00 per 1M input tokens
        "output": 0.06     # $60.00 per 1M output tokens
    },
    "gpt-3.5-turbo": {
        "input": 0.0005,
        "output": 0.0015
    },
    "default": {
        "input": 0.0015,
        "output": 0.002
    }
}

class ContextUtils:
    @staticmethod
    def estimate_llm_cost(model_name: str, input_tokens: int, output_tokens: int = 0) -> float:
        """Estimates LLM API cost in USD based on input/output token counts."""
        normalized_name = (model_name or "default").lower()
        price_config = LLM_PRICING["default"]
        
        for key, config in LLM_PRICING.items():
            if key in normalized_name:
                price_config = config
                break
                
        input_cost = (input_tokens / 1000.0) * price_config["input"]
        output_cost = (output_tokens / 1000.0) * price_config["output"]
        return round(input_cost + output_cost, 6)

    @staticmethod
    def clean_text_whitespace(text: str) -> str:
        """Helper to clean extra spaces and clean formatting for prompt compatibility."""
        if not text:
            return ""
        return " ".join(text.strip().split())
