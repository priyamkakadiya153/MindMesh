import logging
from uuid import UUID
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory.models import LongTermMemory
from app.memory.repository import MemoryRepository
from app.memory.summarizer import MemorySummarizer

logger = logging.getLogger(__name__)

class MemoryConsolidator:
    @staticmethod
    async def consolidate_session_memories(
        db: AsyncSession,
        organization_id: UUID,
        scope_key: str,
        memory_type: str,
        key: str
    ) -> Optional[LongTermMemory]:
        """Consolidates separate records of a given type/key into a single long-term memory."""
        # 1. Fetch matching memories to consolidate
        memories = await MemoryRepository.list_memories(
            db=db,
            organization_id=organization_id,
            memory_type=memory_type,
            scope_key=scope_key,
            key=key
        )

        if len(memories) <= 1:
            return None

        # 2. Extract context payloads
        payloads = [m.value for m in memories]

        # 3. Summarize payloads
        consolidated_payload = MemorySummarizer.merge_payloads(payloads)

        # 4. Remove original separate memory items
        for m in memories:
            await db.delete(m)

        # 5. Create new consolidated memory
        consolidated = LongTermMemory(
            memory_type=memory_type,
            scope_key=scope_key,
            organization_id=organization_id,
            key=key,
            value=consolidated_payload,
            importance_score=0.8,
            confidence_score=1.0,
            last_accessed_at=datetime.utcnow()
        )
        
        db.add(consolidated)
        await db.flush()
        logger.info(f"MemoryConsolidator: Successfully consolidated {len(memories)} memories for key '{key}'.")
        return consolidated
