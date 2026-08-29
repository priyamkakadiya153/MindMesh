import logging
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, and_

from .providers import EmbeddingProviderFactory
from .models import DocumentChunk, DocumentEmbedding
from ...documents.models import Document
from ...documents.exceptions import DocumentNotFoundException

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_document_embeddings(
        self,
        document_id: UUID,
        provider_name: str = "gemini",
        model_name: Optional[str] = None
    ) -> int:
        """Batch generates vector embeddings for all document chunks of a document."""
        logger.info(f"Generating embeddings for document: {document_id} (Provider: {provider_name})")

        # 1. Fetch document
        doc_stmt = select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
        doc = (await self.db.execute(doc_stmt)).scalar_one_or_none()
        if not doc:
            raise DocumentNotFoundException(str(document_id))

        # 2. Fetch document chunks
        chunk_stmt = select(DocumentChunk).where(
            DocumentChunk.document_id == document_id,
            DocumentChunk.deleted_at.is_(None)
        ).order_by(DocumentChunk.chunk_index.asc())

        res_chunks = await self.db.execute(chunk_stmt)
        chunks = res_chunks.scalars().all()

        if not chunks:
            logger.warning(f"No chunks found for document {document_id}. Skipping embedding generation.")
            return 0

        # 3. Instantiate Provider
        provider = EmbeddingProviderFactory.get_provider(provider_name, model_name)

        # 4. Fetch existing embeddings to check checksum match (skip identical ones)
        emb_stmt = select(DocumentEmbedding).where(DocumentEmbedding.document_id == document_id)
        existing_res = await self.db.execute(emb_stmt)
        existing_embeddings = {emb.chunk_id: emb for emb in existing_res.scalars().all()}

        chunks_to_embed: List[DocumentChunk] = []
        for c in chunks:
            existing_emb = existing_embeddings.get(c.id)
            if not existing_emb or existing_emb.checksum != c.checksum or existing_emb.embedding_model != provider.model_name:
                chunks_to_embed.append(c)

        if not chunks_to_embed:
            logger.info(f"All {len(chunks)} chunks for document {document_id} are already embedded with up-to-date checksums.")
            doc.processing_status = "EMBEDDED"
            await self.db.flush()
            return 0

        # 5. Process in batches of 50
        batch_size = 50
        generated_count = 0

        for i in range(0, len(chunks_to_embed), batch_size):
            batch_chunks = chunks_to_embed[i : i + batch_size]
            batch_texts = [c.content for c in batch_chunks]

            vectors = await provider.embed_texts(batch_texts)

            for chunk_obj, vec in zip(batch_chunks, vectors):
                existing_emb = existing_embeddings.get(chunk_obj.id)
                if existing_emb:
                    existing_emb.embedding_model = provider.model_name
                    existing_emb.embedding_dimension = provider.dimension
                    existing_emb.embedding = vec
                    existing_emb.checksum = chunk_obj.checksum
                    existing_emb.embedding_version += 1
                    existing_emb.updated_at = datetime.utcnow()
                else:
                    new_emb = DocumentEmbedding(
                        document_id=document_id,
                        chunk_id=chunk_obj.id,
                        organization_id=doc.organization_id,
                        workspace_id=doc.workspace_id,
                        embedding_model=provider.model_name,
                        embedding_dimension=provider.dimension,
                        embedding_version=1,
                        embedding=vec,
                        checksum=chunk_obj.checksum
                    )
                    self.db.add(new_emb)
                generated_count += 1

            await self.db.flush()

        doc.processing_status = "EMBEDDED"
        await self.db.flush()

        logger.info(f"Successfully generated {generated_count} vector embeddings for document {document_id}")
        return generated_count

    async def get_document_embedding_status(self, document_id: UUID) -> Dict[str, Any]:
        """Returns vector status metadata for a specific document."""
        doc_stmt = select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
        doc = (await self.db.execute(doc_stmt)).scalar_one_or_none()
        if not doc:
            raise DocumentNotFoundException(str(document_id))

        total_chunks = (await self.db.execute(
            select(func.count()).select_from(DocumentChunk).where(DocumentChunk.document_id == document_id, DocumentChunk.deleted_at.is_(None))
        )).scalar() or 0

        emb_stmt = select(DocumentEmbedding).where(DocumentEmbedding.document_id == document_id).order_by(DocumentEmbedding.created_at.desc())
        embeddings = (await self.db.execute(emb_stmt)).scalars().all()
        embedded_count = len(embeddings)

        latest_emb = embeddings[0] if embeddings else None

        return {
            "document_id": document_id,
            "status": "COMPLETED" if (total_chunks > 0 and embedded_count >= total_chunks) else "PENDING",
            "total_chunks": total_chunks,
            "embedded_vectors": embedded_count,
            "embedding_model": latest_emb.embedding_model if latest_emb else "text-embedding-004",
            "dimension": latest_emb.embedding_dimension if latest_emb else 768,
            "version": latest_emb.embedding_version if latest_emb else 1,
            "generated_at": latest_emb.created_at if latest_emb else None
        }

    async def get_workspace_embedding_metrics(
        self,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Returns workspace vector metrics summary."""
        chunk_stmt = select(func.count()).select_from(DocumentChunk).where(
            DocumentChunk.organization_id == organization_id,
            DocumentChunk.deleted_at.is_(None)
        )
        if workspace_id:
            chunk_stmt = chunk_stmt.where(DocumentChunk.workspace_id == workspace_id)

        total_chunks = (await self.db.execute(chunk_stmt)).scalar() or 0

        emb_stmt = select(func.count()).select_from(DocumentEmbedding).where(
            DocumentEmbedding.organization_id == organization_id
        )
        if workspace_id:
            emb_stmt = emb_stmt.where(DocumentEmbedding.workspace_id == workspace_id)

        total_embeddings = (await self.db.execute(emb_stmt)).scalar() or 0

        pending_chunks = max(0, total_chunks - total_embeddings)

        return {
            "organization_id": organization_id,
            "workspace_id": workspace_id,
            "total_chunks": total_chunks,
            "embedded_chunks": total_embeddings,
            "pending_chunks": pending_chunks,
            "completion_percentage": round((total_embeddings / total_chunks * 100), 1) if total_chunks > 0 else 100.0,
            "default_model": "text-embedding-004"
        }
