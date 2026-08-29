import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ChatAnalytics:
    @staticmethod
    def log_request_metrics(
        chat_id: str,
        provider: str,
        model: str,
        latency_ms: int,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float
    ) -> None:
        """Logs request telemetry to system monitors."""
        logger.info(
            f"[AI CHAT METRICS] Session={chat_id} Provider={provider} Model={model} "
            f"Latency={latency_ms}ms PromptTokens={prompt_tokens} CompletionTokens={completion_tokens} "
            f"Cost=${cost:.6f}"
        )
