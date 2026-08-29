import asyncio
from typing import Dict, Set, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger("mindmesh.typing")

class TypingService:
    def __init__(self):
        # Maps conversation_id -> { user_id -> {"user_name": str, "timer": Task, "started_at": datetime} }
        self.typing_map: Dict[str, Dict[str, dict]] = {}
        self.TIMEOUT_SECONDS = 4.0

    def start_typing(self, conversation_id: str, user_id: str, user_name: str, on_timeout_callback=None):
        if conversation_id not in self.typing_map:
            self.typing_map[conversation_id] = {}

        # Cancel existing timer task if present
        if user_id in self.typing_map[conversation_id]:
            old_timer = self.typing_map[conversation_id][user_id].get("timer")
            if old_timer and not old_timer.done():
                old_timer.cancel()

        # Create background auto-expiration timer
        async def _timeout_task():
            await asyncio.sleep(self.TIMEOUT_SECONDS)
            self.stop_typing(conversation_id, user_id)
            if on_timeout_callback:
                try:
                    await on_timeout_callback(conversation_id, user_id)
                except Exception as e:
                    logger.error(f"Error in typing timeout callback: {e}")

        task = asyncio.create_task(_timeout_task())
        self.typing_map[conversation_id][user_id] = {
            "user_name": user_name,
            "timer": task,
            "started_at": datetime.utcnow()
        }

    def stop_typing(self, conversation_id: str, user_id: str):
        if conversation_id in self.typing_map and user_id in self.typing_map[conversation_id]:
            task = self.typing_map[conversation_id][user_id].get("timer")
            if task and not task.done():
                task.cancel()
            del self.typing_map[conversation_id][user_id]
            if not self.typing_map[conversation_id]:
                del self.typing_map[conversation_id]

    def get_typing_users(self, conversation_id: str) -> List[dict]:
        if conversation_id not in self.typing_map:
            return []
        return [
            {"user_id": uid, "user_name": data["user_name"]}
            for uid, data in self.typing_map[conversation_id].items()
        ]

typing_service = TypingService()
