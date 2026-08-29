import asyncio
from typing import Dict, Any
from app.agents.collaboration.context import SharedContext

class ContextSynchronizer:
    def __init__(self):
        self._lock = asyncio.Lock()

    async def update_memory(self, context: SharedContext, key: str, value: Any):
        """Thread-safe / async-safe modification of context memory."""
        async with self._lock:
            context.memory[key] = value

    async def append_knowledge(self, context: SharedContext, citation: Dict[str, Any]):
        """Thread-safe / async-safe appending of retrieved knowledge."""
        async with self._lock:
            context.retrieved_knowledge.append(citation)
