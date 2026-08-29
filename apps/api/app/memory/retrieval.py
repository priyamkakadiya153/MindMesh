import logging
from uuid import UUID
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory.repository import MemoryRepository
from app.memory.ranking import MemoryRanker
from app.memory.policies import MemoryPermissionPolicy

logger = logging.getLogger(__name__)

class MemoryRetrieval:
    @staticmethod
    async def retrieve_context(
        db: AsyncSession,
        organization_id: UUID,
        user_id: UUID,
        project_id: Optional[UUID] = None,
        workspace_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None,
        query_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves and ranks relevant memories based on access hierarchy rules."""
        # 1. Fetch memories from scopes
        memories = []
        
        # User Scope
        user_memories = await MemoryRepository.list_memories(
            db, organization_id, memory_type="User", scope_key=str(user_id), key=query_key
        )
        memories.extend(user_memories)

        # Project Scope
        if project_id:
            proj_memories = await MemoryRepository.list_memories(
                db, organization_id, memory_type="Project", scope_key=str(project_id), key=query_key
            )
            memories.extend(proj_memories)

        # Organization Scope
        org_memories = await MemoryRepository.list_memories(
            db, organization_id, memory_type="Organization", scope_key=str(organization_id), key=query_key
        )
        memories.extend(org_memories)

        # Agent Scope
        if agent_id:
            agent_memories = await MemoryRepository.list_memories(
                db, organization_id, memory_type="Agent", scope_key=str(agent_id), key=query_key
            )
            memories.extend(agent_memories)

        # 2. Filter out expired memories
        now = datetime.utcnow()
        active_memories = [
            m for m in memories 
            if m.retention_expires_at is None or m.retention_expires_at > now
        ]

        # 3. Filter by agent permissions
        allowed_memories = [
            m for m in active_memories
            if MemoryPermissionPolicy.can_access(m, str(user_id))
        ]

        # 4. Rank memories
        ranked = MemoryRanker.rank_memories(allowed_memories)

        # 5. Update last_accessed_at and return
        results = []
        for m in ranked:
            m.last_accessed_at = now
            results.append({
                "id": str(m.id),
                "memory_type": m.memory_type,
                "key": m.key,
                "value": m.value,
                "confidence": m.confidence_score,
                "importance": m.importance_score
            })
            
        await db.flush()
        return results
