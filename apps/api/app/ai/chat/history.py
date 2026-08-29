import logging
from uuid import UUID
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.ai.conversation.history import ConversationHistoryManager

logger = logging.getLogger(__name__)

class ChatHistoryLoader:
    @staticmethod
    async def load_and_format_history(
        db: AsyncSession,
        chat_id: UUID,
        limit_count: int = 20,
        token_limit: int = 4000
    ) -> List[Dict[str, str]]:
        """Loads most recent messages for a chat ID and formats them for the LLM prompt."""
        # Query messages sorted chronologically (we want the tail of the conversation)
        # Note: Message model uses sender_id. If sender_id matches user, role is 'user', else 'assistant'
        stmt = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .limit(limit_count)
        )
        res = await db.execute(stmt)
        messages_records = list(res.scalars().all())
        
        # We queried desc, reverse back to asc chronological order
        messages_records.reverse()
        
        formatted = []
        for msg in messages_records:
            # We can infer role:
            # If msg.sender_id is present, it's user, else it's assistant
            role = msg.role if (msg.role and msg.role in ["user", "assistant", "system"]) else ("user" if msg.sender_id else "assistant")
            formatted.append({
                "role": role,
                "content": msg.content or ""
            })
            
        # Apply trimming to stay inside token budget
        return ConversationHistoryManager.trim_history(formatted, history_token_limit=token_limit)
