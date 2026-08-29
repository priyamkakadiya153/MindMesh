import logging
from uuid import UUID
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory.models import LongTermMemory
from app.memory.repository import MemoryRepository
from app.memory.retrieval import MemoryRetrieval
from app.memory.retention import MemoryRetentionManager

logger = logging.getLogger(__name__)

class MemoryService:
    @staticmethod
    async def add_memory(
        db: AsyncSession,
        organization_id: UUID,
        memory_type: str,
        scope_key: str,
        key: str,
        value: Dict[str, Any],
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        importance_score: float = 0.5,
        confidence_score: float = 1.0,
        retention_days: Optional[int] = None
    ) -> LongTermMemory:
        """Stores a long-term memory with strict org tenant boundary check."""
        expires = None
        if retention_days:
            expires = datetime.utcnow() + timedelta(days=retention_days)

        memory = LongTermMemory(
            memory_type=memory_type,
            scope_key=scope_key,
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            key=key,
            value=value,
            importance_score=importance_score,
            confidence_score=confidence_score,
            retention_expires_at=expires,
            last_accessed_at=datetime.utcnow()
        )
        
        await MemoryRepository.create_memory(db, memory)
        logger.info(f"MemoryService: Added {memory_type} memory for key '{key}' under org '{organization_id}'")
        return memory

    @staticmethod
    async def search_memories(
        db: AsyncSession,
        organization_id: UUID,
        user_id: UUID,
        project_id: Optional[UUID] = None,
        workspace_id: Optional[UUID] = None,
        query_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Invokes retrievals matching hierarchal priority gates."""
        return await MemoryRetrieval.retrieve_context(
            db=db,
            organization_id=organization_id,
            user_id=user_id,
            project_id=project_id,
            workspace_id=workspace_id,
            query_key=query_key
        )

    @staticmethod
    async def forget_memory(db: AsyncSession, memory_id: UUID) -> bool:
        """Manually deletes a memory record."""
        return await MemoryRepository.delete_memory(db, memory_id)
