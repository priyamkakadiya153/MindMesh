import logging
from uuid import UUID
from typing import Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory.models import LongTermMemory

logger = logging.getLogger(__name__)

class MemoryAnalytics:
    @staticmethod
    async def get_storage_stats(db: AsyncSession, organization_id: UUID) -> Dict[str, Any]:
        """Calculates total memory records and groups by scope type."""
        stmt = select(LongTermMemory.memory_type, func.count(LongTermMemory.id)).where(
            LongTermMemory.organization_id == organization_id
        ).group_by(LongTermMemory.memory_type)

        res = await db.execute(stmt)
        counts = dict(res.all())

        total = sum(counts.values())

        return {
            "total_memory_records": total,
            "memory_by_type": counts,
            "retrieval_latency_ms": 12.5,  # mock telemetry latency
            "consolidation_runs": 3
        }
