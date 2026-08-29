import logging
from typing import List, Dict
from ..context.tokenizer import TokenBudgetManager

logger = logging.getLogger(__name__)

class ConversationHistoryManager:
    @staticmethod
    def trim_history(
        messages: List[Dict[str, str]],
        history_token_limit: int = 1500
    ) -> List[Dict[str, str]]:
        """Trims conversation history from the beginning to fit within token limit.
        
        Ensures we keep the most recent messages.
        """
        if not messages:
            return []
            
        trimmed = []
        accumulated_tokens = 0
        
        # Traverse messages backwards (most recent first)
        for msg in reversed(messages):
            tokens = TokenBudgetManager.count_tokens(msg.get("content", ""))
            if accumulated_tokens + tokens <= history_token_limit:
                trimmed.append(msg)
                accumulated_tokens += tokens
            else:
                # We can try to partially include/truncate if it's the very latest message
                if not trimmed:
                    # Truncate content to fit limit
                    content = msg.get("content", "")
                    truncated_content = content[:history_token_limit * 4] + "..."
                    truncated_msg = msg.copy()
                    truncated_msg["content"] = truncated_content
                    trimmed.append(truncated_msg)
                break
                
        # Return in original chronological order
        return list(reversed(trimmed))
