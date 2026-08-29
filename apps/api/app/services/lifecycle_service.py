from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..documents.models import Document, RetentionPolicy
from ..documents.exceptions import DocumentNotFoundException
from ..documents.enums import ProcessingStatus
from ..documents.audit import AuditLogger

class LifecycleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit = AuditLogger(db)

    async def archive(self, document_id: UUID, user_id: UUID) -> Document:
        stmt = select(Document).where(Document.id == document_id, Document.is_active == True)
        doc = (await self.db.execute(stmt)).scalar_one_or_none()
        if not doc:
            raise DocumentNotFoundException(str(document_id))

        doc.processing_status = ProcessingStatus.ARCHIVED
        await self.audit.log_action(
            document_id=document_id,
            user_id=user_id,
            action="ARCHIVE",
            metadata={"status": ProcessingStatus.ARCHIVED}
        )
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def restore(self, document_id: UUID, user_id: UUID) -> Document:
        stmt = select(Document).where(Document.id == document_id)
        doc = (await self.db.execute(stmt)).scalar_one_or_none()
        if not doc:
            raise DocumentNotFoundException(str(document_id))

        # Restore active flag and set back status to READY
        doc.is_active = True
        doc.processing_status = ProcessingStatus.READY
        
        await self.audit.log_action(
            document_id=document_id,
            user_id=user_id,
            action="RESTORE",
            metadata={"status": ProcessingStatus.READY}
        )
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def soft_delete(self, document_id: UUID, user_id: UUID) -> bool:
        stmt = select(Document).where(Document.id == document_id, Document.is_active == True)
        doc = (await self.db.execute(stmt)).scalar_one_or_none()
        if not doc:
            raise DocumentNotFoundException(str(document_id))

        doc.is_active = False
        doc.deleted_at = datetime.utcnow()
        
        await self.audit.log_action(
            document_id=document_id,
            user_id=user_id,
            action="DELETE"
        )
        await self.db.commit()
        return True

    async def apply_retention(self, org_id: UUID) -> int:
        """Applies retention policy settings to automatically archive or delete documents."""
        stmt_p = select(RetentionPolicy).where(RetentionPolicy.organization_id == org_id)
        policy = (await self.db.execute(stmt_p)).scalar_one_or_none()
        if not policy:
            return 0

        cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_days)
        
        # Query docs matching criteria
        stmt_docs = select(Document).where(
            Document.organization_id == org_id,
            Document.created_at < cutoff_date,
            Document.is_active == True
        )
        docs = (await self.db.execute(stmt_docs)).scalars().all()
        
        affected = 0
        for doc in docs:
            if policy.auto_delete:
                doc.is_active = False
                doc.deleted_at = datetime.utcnow()
                await self.audit.log_action(doc.id, doc.uploaded_by, "DELETE", {"reason": "retention_policy"})
                affected += 1
            elif policy.auto_archive and doc.processing_status != ProcessingStatus.ARCHIVED:
                doc.processing_status = ProcessingStatus.ARCHIVED
                await self.audit.log_action(doc.id, doc.uploaded_by, "ARCHIVE", {"reason": "retention_policy"})
                affected += 1
                
        if affected > 0:
            await self.db.commit()
            
        return affected
