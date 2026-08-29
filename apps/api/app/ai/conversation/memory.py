import logging
from uuid import UUID
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.conversation import ConversationMemory

logger = logging.getLogger(__name__)

class ConversationMemoryManager:
    @staticmethod
    async def load_memory(
        db: AsyncSession,
        chat_id: UUID
    ) -> Optional[ConversationMemory]:
        """Loads ConversationMemory record for a chat/conversation ID."""
        try:
            stmt = select(ConversationMemory).where(
                ConversationMemory.chat_id == chat_id,
                ConversationMemory.is_active == True
            )
            res = await db.execute(stmt)
            return res.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error loading conversation memory for chat {chat_id}: {str(e)}")
            return None

    @staticmethod
    async def save_memory(
        db: AsyncSession,
        chat_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> ConversationMemory:
        """Saves or updates ConversationMemory record for a chat/conversation ID."""
        stmt = select(ConversationMemory).where(ConversationMemory.chat_id == chat_id)
        res = await db.execute(stmt)
        memory = res.scalar_one_or_none()
        
        if not memory:
            memory = ConversationMemory(
                chat_id=chat_id,
                workspace_id=workspace_id,
                project_id=project_id,
                context_data=context_data or {}
            )
            db.add(memory)
        else:
            if workspace_id is not None:
                memory.workspace_id = workspace_id
            if project_id is not None:
                memory.project_id = project_id
            if context_data is not None:
                existing = memory.context_data or {}
                existing.update(context_data)
                memory.context_data = existing
        await db.flush()
        return memory

    @staticmethod
    async def update_context(
        db: AsyncSession,
        chat_id: UUID,
        org_id: UUID,
        user_message: str,
        assistant_response: str
    ) -> Optional[ConversationMemory]:
        """Updates conversation context data in ConversationMemory."""
        return await ConversationMemoryManager.save_memory(
            db=db,
            chat_id=chat_id,
            context_data={
                "last_user_message": user_message[:200],
                "last_assistant_response": assistant_response[:200]
            }
        )
