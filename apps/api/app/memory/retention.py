import logging
from uuid import UUID
from datetime import datetime
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory.models import LongTermMemory

logger = logging.getLogger(__name__)

class MemoryRetentionManager:
    @staticmethod
    async def purge_expired_memories(db: AsyncSession) -> int:
        """Deletes memories that have crossed their expiration time."""
        now = datetime.utcnow()
        stmt = delete(LongTermMemory).where(
            LongTermMemory.retention_expires_at != None,
            LongTermMemory.retention_expires_at <= now
        )
        res = await db.execute(stmt)
        await db.flush()
        count = res.rowcount or 0
        if count > 0:
            logger.info(f"MemoryRetentionManager: Purged {count} expired memory records.")
        return count

    @staticmethod
    async def force_forget_user_memory(db: AsyncSession, organization_id: UUID, user_id: UUID) -> int:
        """Enforces compliance with GDPR Right to be Forgotten by purging all user memory."""
        stmt = delete(LongTermMemory).where(
            LongTermMemory.organization_id == organization_id,
            LongTermMemory.memory_type == "User",
            LongTermMemory.scope_key == str(user_id)
        )
        res = await db.execute(stmt)
        await db.flush()
        count = res.rowcount or 0
        logger.info(f"MemoryRetentionManager: GDPR force forgot {count} user memory records for user '{user_id}'.")
        return count
