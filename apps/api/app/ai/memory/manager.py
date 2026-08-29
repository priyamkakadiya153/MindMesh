import uuid
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from .models import ConversationMemory, ConversationSummary

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages workspace and conversation memories with ranking and prompt injection."""

    @staticmethod
    async def add_memory(
        db: AsyncSession,
        workspace_id: UUID,
        organization_id: UUID,
        content: str,
        conversation_id: Optional[UUID] = None,
        memory_type: str = "fact",
        importance: int = 3,
        is_pinned: bool = False
    ) -> ConversationMemory:
        """Stores a new long-term memory item."""
        mem = ConversationMemory(
            id=uuid.uuid4(),
            chat_id=conversation_id,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            organization_id=organization_id,
            memory_type=memory_type,
            importance=max(1, min(5, importance)),
            content=content,
            is_pinned=is_pinned,
            expiration_status="permanent"
        )
        db.add(mem)
        await db.commit()
        await db.refresh(mem)
        return mem

    @staticmethod
    async def pin_memory(db: AsyncSession, memory_id: UUID, is_pinned: bool = True) -> Optional[ConversationMemory]:
        """Pins or unpins a memory item."""
        stmt = select(ConversationMemory).where(ConversationMemory.id == memory_id)
        mem = (await db.execute(stmt)).scalar_one_or_none()
        if mem:
            mem.is_pinned = is_pinned
            await db.commit()
            await db.refresh(mem)
        return mem

    @staticmethod
    async def delete_memory(db: AsyncSession, memory_id: UUID) -> bool:
        """Deletes a memory item."""
        stmt = select(ConversationMemory).where(ConversationMemory.id == memory_id)
        mem = (await db.execute(stmt)).scalar_one_or_none()
        if mem:
            await db.delete(mem)
            await db.commit()
            return True
        return False

    @staticmethod
    async def rank_and_select_memories(
        db: AsyncSession,
        workspace_id: UUID,
        organization_id: UUID,
        conversation_id: Optional[UUID] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Ranks memories by pinned status, importance (1-5), and recency."""
        # 1. Fetch pinned memories
        pinned_stmt = select(ConversationMemory).where(
            ConversationMemory.workspace_id == workspace_id,
            ConversationMemory.organization_id == organization_id,
            ConversationMemory.is_pinned.is_(True),
            ConversationMemory.deleted_at.is_(None)
        ).order_by(desc(ConversationMemory.importance), desc(ConversationMemory.created_at)).limit(top_k)

        pinned_memories = (await db.execute(pinned_stmt)).scalars().all()
        selected_ids = {m.id for m in pinned_memories}

        # 2. Fetch unpinned memories if top_k not filled
        remaining_k = max(0, top_k - len(pinned_memories))
        unpinned_memories = []
        if remaining_k > 0:
            unpinned_stmt = select(ConversationMemory).where(
                ConversationMemory.workspace_id == workspace_id,
                ConversationMemory.organization_id == organization_id,
                ConversationMemory.is_pinned.is_(False),
                ConversationMemory.deleted_at.is_(None)
            ).order_by(desc(ConversationMemory.importance), desc(ConversationMemory.created_at)).limit(remaining_k)
            unpinned_memories = (await db.execute(unpinned_stmt)).scalars().all()

        all_memories = list(pinned_memories) + list(unpinned_memories)

        # 3. Format Memory Context for Prompt Builder
        memory_lines = []
        for m in all_memories:
            tag = "[PINNED] " if m.is_pinned else ""
            memory_lines.append(f"- {tag}{m.content}")

        memory_prompt_text = "\n".join(memory_lines) if memory_lines else "No pinned workspace memories available."

        return {
            "memories": all_memories,
            "memory_prompt_text": memory_prompt_text,
            "count": len(all_memories)
        }
