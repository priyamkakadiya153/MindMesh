import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ..ai.embeddings.service import EmbeddingService
from ..ai.embeddings.models import DocumentChunk, DocumentEmbedding
from ..documents.models import Document

logger = logging.getLogger(__name__)

class LifecycleManager:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.emb_service = EmbeddingService(db)

    async def delete_vectors(self, document_id: UUID) -> int:
        """Deletes all chunks and embeddings associated with a document."""
        stmt = select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        res = await self.db.execute(stmt)
        chunks = res.scalars().all()
        count = len(chunks)
        
        stmt_del = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        await self.db.execute(stmt_del)
        await self.db.commit()
        
        from .metrics import metrics_manager
        metrics_manager.record_delete(count)
        return count

    async def synchronize(self, org_id: UUID) -> dict:
        """Finds active documents in organization missing embeddings, and generates them."""
        stmt = select(Document).where(Document.organization_id == org_id, Document.is_active == True)
        res = await self.db.execute(stmt)
        docs = res.scalars().all()
        
        synced_count = 0
        failed_count = 0
        processed_docs = []
        
        for doc in docs:
            stmt_c = select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
            res_c = await self.db.execute(stmt_c)
            chunks = res_c.scalars().all()
            
            needs_generation = False
            if not chunks:
                needs_generation = True
            else:
                stmt_e = select(DocumentEmbedding).join(
                    DocumentChunk, DocumentChunk.id == DocumentEmbedding.chunk_id
                ).where(DocumentChunk.document_id == doc.id)
                res_e = await self.db.execute(stmt_e)
                embs = res_e.scalars().all()
                if len(embs) < len(chunks):
                    needs_generation = True
                    
            if needs_generation:
                try:
                    from ..processing.models import DocumentContent
                    stmt_cnt = select(DocumentContent).where(DocumentContent.document_id == doc.id)
                    cnt = (await self.db.execute(stmt_cnt)).scalar_one_or_none()
                    if cnt:
                        await self.emb_service.generate_document_embeddings(doc.id)
                        synced_count += 1
                        processed_docs.append(str(doc.id))
                except Exception as e:
                    logger.error(f"Sync failed for document {doc.id}: {e}")
                    failed_count += 1
                    
        return {
            "synced_documents_count": synced_count,
            "failed_documents_count": failed_count,
            "processed_documents": processed_docs
        }

    async def rebuild_all_vectors(self, org_id: UUID) -> dict:
        """Regenerates all chunks and embeddings for all active documents in organization."""
        stmt = select(Document).where(Document.organization_id == org_id, Document.is_active == True)
        res = await self.db.execute(stmt)
        docs = res.scalars().all()
        
        success_count = 0
        failed_count = 0
        processed_docs = []
        
        for doc in docs:
            try:
                from ..processing.models import DocumentContent
                stmt_cnt = select(DocumentContent).where(DocumentContent.document_id == doc.id)
                cnt = (await self.db.execute(stmt_cnt)).scalar_one_or_none()
                if cnt:
                    await self.emb_service.generate_document_embeddings(doc.id)
                    success_count += 1
                    processed_docs.append(str(doc.id))
            except Exception as e:
                logger.error(f"Rebuild failed for document {doc.id}: {e}")
                failed_count += 1
                
        return {
            "rebuilt_documents_count": success_count,
            "failed_documents_count": failed_count,
            "processed_documents": processed_docs
        }
