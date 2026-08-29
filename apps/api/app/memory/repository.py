import logging
from uuid import UUID
from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory.models import LongTermMemory

logger = logging.getLogger(__name__)

class MemoryRepository:
    @staticmethod
    async def create_memory(db: AsyncSession, memory: LongTermMemory) -> LongTermMemory:
        db.add(memory)
        await db.flush()
        return memory

    @staticmethod
    async def get_memory(db: AsyncSession, memory_id: UUID) -> Optional[LongTermMemory]:
        stmt = select(LongTermMemory).where(LongTermMemory.id == memory_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def delete_memory(db: AsyncSession, memory_id: UUID) -> bool:
        stmt = delete(LongTermMemory).where(LongTermMemory.id == memory_id)
        res = await db.execute(stmt)
        await db.flush()
        return (res.rowcount or 0) > 0

    @staticmethod
    async def list_memories(
        db: AsyncSession,
        organization_id: UUID,
        memory_type: Optional[str] = None,
        scope_key: Optional[str] = None,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        key: Optional[str] = None
    ) -> List[LongTermMemory]:
        """Queries memories under strict organization/tenant isolation boundaries."""
        stmt = select(LongTermMemory).where(LongTermMemory.organization_id == organization_id)
        
        if memory_type:
            stmt = stmt.where(LongTermMemory.memory_type == memory_type)
        if scope_key:
            stmt = stmt.where(LongTermMemory.scope_key == scope_key)
        if workspace_id:
            stmt = stmt.where(LongTermMemory.workspace_id == workspace_id)
        if project_id:
            stmt = stmt.where(LongTermMemory.project_id == project_id)
        if key:
            stmt = stmt.where(LongTermMemory.key == key)

        res = await db.execute(stmt)
        return list(res.scalars().all())
