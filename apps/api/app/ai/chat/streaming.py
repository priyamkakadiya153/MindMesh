import json
from typing import AsyncGenerator, Dict, Any

class ChatStreamer:
    @staticmethod
    async def format_sse_stream(
        generator: AsyncGenerator[Dict[str, Any], None]
    ) -> AsyncGenerator[str, None]:
        """Wraps RAG stream dictionary outputs into SSE formatted string payloads."""
        async for chunk in generator:
            # Yield as SSE event
            yield f"data: {json.dumps(chunk, default=str)}\n\n"
        yield "event: close\ndata: \n\n"
