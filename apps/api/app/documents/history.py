from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from .models import DocumentAuditLog

class HistoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_audit_history(self, document_id: UUID) -> List[DocumentAuditLog]:
        stmt = select(DocumentAuditLog).where(DocumentAuditLog.document_id == document_id).order_by(desc(DocumentAuditLog.timestamp))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
