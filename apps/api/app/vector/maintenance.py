import logging
from uuid import UUID
from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from ..ai.embeddings.models import DocumentEmbedding, DocumentChunk
from ..documents.models import Document

logger = logging.getLogger(__name__)

class MaintenanceManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def optimize_indexes(self, org_id: UUID) -> dict:
        """Optimizes database indexes (e.g. VACUUM, ANALYZE, REINDEX)."""
        dialect_name = self.db.bind.dialect.name if self.db.bind else "sqlite"
        if dialect_name == "postgresql":
            try:
                # Commit current transaction since REINDEX cannot run inside transaction blocks
                await self.db.commit()
                await self.db.execute(text("REINDEX TABLE document_embeddings"))
                return {
                    "status": "success",
                    "message": "Index defragmentation (REINDEX) completed successfully."
                }
            except Exception as e:
                logger.error(f"Postgres index optimization failed: {e}")
                return {
                    "status": "error",
                    "message": f"Postgres index optimization failed: {str(e)}"
                }
        else:
            try:
                await self.db.execute(text("ANALYZE"))
                return {
                    "status": "success",
                    "message": "SQLite ANALYZE optimization completed successfully."
                }
            except Exception as e:
                logger.error(f"SQLite optimization failed: {e}")
                return {
                    "status": "error",
                    "message": f"SQLite optimization failed: {str(e)}"
                }

    async def cleanup_orphaned_vectors(self, org_id: UUID) -> dict:
        """Removes embeddings where the chunk or parent document is missing or soft-deleted."""
        # 1. Clean orphaned embeddings (no corresponding chunk exists)
        stmt_orphaned = select(DocumentEmbedding.id).outerjoin(
            DocumentChunk, DocumentChunk.id == DocumentEmbedding.chunk_id
        ).where(DocumentChunk.id == None)
        
        res_orphaned = await self.db.execute(stmt_orphaned)
        orphaned_ids = res_orphaned.scalars().all()
        
        deleted_count = 0
        if orphaned_ids:
            stmt_del = delete(DocumentEmbedding).where(DocumentEmbedding.id.in_(orphaned_ids))
            res_del = await self.db.execute(stmt_del)
            deleted_count = res_del.rowcount
            await self.db.commit()

        # 2. Clean chunks and embeddings belonging to soft-deleted/inactive documents
        stmt_inactive = select(DocumentChunk.id).join(
            Document, Document.id == DocumentChunk.document_id
        ).where(Document.is_active == False)
        
        res_inactive = await self.db.execute(stmt_inactive)
        inactive_ids = res_inactive.scalars().all()
        
        if inactive_ids:
            stmt_del_c = delete(DocumentChunk).where(DocumentChunk.id.in_(inactive_ids))
            res_del_c = await self.db.execute(stmt_del_c)
            deleted_count += res_del_c.rowcount
            await self.db.commit()
            
        return {
            "orphaned_vectors_deleted": deleted_count
        }
