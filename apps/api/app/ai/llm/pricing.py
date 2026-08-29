from typing import Dict

# Pricing per 1,000,000 tokens in USD
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # OpenAI Models
    "gpt-4o": {
        "input": 5.00,
        "output": 15.00
    },
    "gpt-4-turbo": {
        "input": 10.00,
        "output": 30.00
    },
    "gpt-3.5-turbo": {
        "input": 0.50,
        "output": 1.50
    },
    # Anthropic Models
    "claude-3-5-sonnet": {
        "input": 3.00,
        "output": 15.00
    },
    "claude-3-opus": {
        "input": 15.00,
        "output": 75.00
    },
    # Google Models
    "gemini-2.0-flash": {
        "input": 0.15,
        "output": 0.60
    },
    "gemini-1.5-pro": {
        "input": 3.50,
        "output": 10.50
    },
    # Local & Gateway Fallback Models
    "ollama": {
        "input": 0.00,
        "output": 0.00
    },
    "default": {
        "input": 1.50,
        "output": 2.00
    }
}
