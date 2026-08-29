import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseStreamingTransport(ABC):
    @abstractmethod
    def format_event(self, event_type: str, data: Dict[str, Any]) -> Any:
        """Formats event type and payload into transport frame."""
        pass

class SSETransport(BaseStreamingTransport):
    """Server-Sent Events (SSE) transport formatter emitting event: type\\ndata: json\\n\\n."""

    def format_event(self, event_type: str, data: Dict[str, Any]) -> str:
        payload = {"event": event_type, **data}
        return f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"

    @classmethod
    def format_connected(cls, stream_id: str, provider: str, model: str) -> str:
        return cls().format_event("connected", {
            "stream_id": stream_id,
            "provider": provider,
            "model": model,
            "timestamp": time.time()
        })

    @classmethod
    def format_token(cls, delta: str, accumulated: str) -> str:
        return cls().format_event("token", {
            "delta": delta,
            "accumulated": accumulated
        })

    @classmethod
    def format_progress(cls, tokens_streamed: int) -> str:
        return cls().format_event("progress", {
            "tokens_streamed": tokens_streamed
        })

    @classmethod
    def format_completed(cls, message_id: str, total_tokens: int, latency_ms: int) -> str:
        return cls().format_event("completed", {
            "message_id": message_id,
            "total_tokens": total_tokens,
            "latency_ms": latency_ms,
            "timestamp": time.time()
        })

    @classmethod
    def format_cancelled(cls, partial_text: str) -> str:
        return cls().format_event("cancelled", {
            "partial_text": partial_text,
            "message": "Generation stopped by user.",
            "timestamp": time.time()
        })

    @classmethod
    def format_error(cls, message: str) -> str:
        return cls().format_event("error", {
            "message": message,
            "timestamp": time.time()
        })

    @classmethod
    def format_heartbeat(cls) -> str:
        return cls().format_event("heartbeat", {
            "timestamp": time.time()
        })

class WebSocketTransport(BaseStreamingTransport):
    """WebSocket transport formatter emitting JSON payload frames."""

    def format_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "event": event_type,
            "timestamp": time.time(),
            **data
        }
