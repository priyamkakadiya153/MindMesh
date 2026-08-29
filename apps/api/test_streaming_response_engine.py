import asyncio
import os
import sys
import uuid
import json

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal, engine
from app.models.organization import Organization
from app.workspace.models import Workspace
from app.ai.llm.base import LLMSettings
from app.ai.llm.factory import LLMProviderFactory
from app.ai.streaming.transport import SSETransport, WebSocketTransport

async def test_streaming_engine():
    print("--- Starting MindMesh Phase 3.7 AI Streaming Response Engine Test ---")

    # 1. Test SSE & WebSocket Transport Frame Formatters
    conn_frame = SSETransport.format_connected("stream-123", "gemini", "gemini-2.5-flash")
    assert "event: connected" in conn_frame
    assert "stream_id" in conn_frame

    token_frame = SSETransport.format_token("Hello ", "Hello ")
    assert "event: token" in token_frame
    assert "Hello " in token_frame

    comp_frame = SSETransport.format_completed("msg-123", 42, 350)
    assert "event: completed" in comp_frame

    ws_transport = WebSocketTransport()
    ws_frame = ws_transport.format_event("token", {"delta": "test", "accumulated": "test"})
    assert ws_frame["event"] == "token"
    assert ws_frame["delta"] == "test"
    print("--> Verified Transport Abstraction & Event Schemas (SSE & WebSocket frame formatters).")

    # 2. Test Provider-Independent Token Generators across Adapters
    providers = ["mock", "gemini", "openai", "claude", "ollama"]
    for p_name in providers:
        adapter = LLMProviderFactory.get_provider(p_name)
        prompt = "Explain streaming architecture in MindMesh."

        tokens_received = []
        async for token_delta in adapter.stream_generate(prompt):
            tokens_received.append(token_delta)
            if len(tokens_received) >= 5:
                break

        assert len(tokens_received) > 0
        print(f"--> Verified Streaming Generator for Provider '{p_name}' (Received {len(tokens_received)} token deltas).")

    print("=== MindMesh Phase 3.7 AI Streaming Response Engine Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(test_streaming_engine())
