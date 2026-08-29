from typing import Dict, Any, Optional

class ConversationStateManager:
    """Manages ephemeral in-memory conversation state indicators."""
    def __init__(self):
        self._states: Dict[str, Dict[str, Any]] = {}

    def set_typing_status(self, chat_id: str, user_id: str, is_typing: bool) -> None:
        self._states.setdefault(chat_id, {})["typing_users"] = {user_id: is_typing}

    def get_typing_status(self, chat_id: str) -> Dict[str, bool]:
        return self._states.get(chat_id, {}).get("typing_users", {})

    def clear_state(self, chat_id: str) -> None:
        if chat_id in self._states:
            del self._states[chat_id]

state_manager = ConversationStateManager()
