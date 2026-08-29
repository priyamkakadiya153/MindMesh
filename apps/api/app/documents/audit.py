from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from .models import DocumentAuditLog

class AuditLogger:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(
        self,
        document_id: UUID,
        user_id: UUID,
        action: str,
        metadata: Optional[dict] = None
    ) -> DocumentAuditLog:
        log = DocumentAuditLog(
            document_id=document_id,
            user_id=user_id,
            action=action,
            action_metadata=metadata
        )

        self.db.add(log)
        await self.db.flush()
        return log
