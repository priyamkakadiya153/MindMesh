import logging
import time
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from .cleaner import TextCleaner
from .chunker import SemanticChunker
from .parser_factory import ParserFactory
from .normalizer import ContentNormalizer
from .models import DocumentContent
from ..documents.models import Document, DocumentProcessingJob
from ..ai.embeddings.models import DocumentChunk
from ..documents.exceptions import DocumentNotFoundException
from ..storage.factory import StorageProviderFactory

logger = logging.getLogger(__name__)

class ProcessingPipeline:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_processing_job(self, document_id: UUID) -> DocumentProcessingJob:
        """Retrieves active job or creates a new QUEUED processing job."""
        stmt = select(DocumentProcessingJob).where(
            DocumentProcessingJob.document_id == document_id,
            DocumentProcessingJob.deleted_at.is_(None)
        ).order_by(DocumentProcessingJob.created_at.desc())
        
        res = await self.db.execute(stmt)
        job = res.scalars().first()

        if not job or job.status in ("COMPLETED", "FAILED"):
            job = DocumentProcessingJob(
                document_id=document_id,
                status="QUEUED",
                progress=0.0,
                started_at=None,
                completed_at=None,
                error_message=None,
                retry_count=0,
                processing_time_ms=0
            )
            self.db.add(job)
            await self.db.flush()

        return job

    async def process_document(self, document_id: UUID) -> DocumentProcessingJob:
        """Executes full 5-stage document text extraction & intelligent chunking pipeline."""
        start_time = time.time()
        logger.info(f"Starting Ingestion Pipeline for document: {document_id}")

        job = await self.get_or_create_processing_job(document_id)
        job.status = "PROCESSING"
        job.progress = 10.0
        job.started_at = datetime.utcnow()
        await self.db.flush()

        # Fetch document
        doc_stmt = select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
        doc = (await self.db.execute(doc_stmt)).scalar_one_or_none()
        if not doc:
            job.status = "FAILED"
            job.error_message = f"Document {document_id} not found."
            await self.db.flush()
            raise DocumentNotFoundException(str(document_id))

        doc.processing_status = "PROCESSING"
        await self.db.flush()

        try:
            # Stage 1: Download from storage provider (10% -> 25%)
            storage = StorageProviderFactory.get_provider()
            file_content = await storage.download(doc.storage_path)
            job.progress = 25.0
            await self.db.flush()

            # Stage 2: Extract text & metadata via ParserFactory (25% -> 45%)
            parser = ParserFactory.get_parser(doc.extension, doc.mime_type)
            raw_parsed = parser.parse(file_content)
            normalized = ContentNormalizer.normalize(raw_parsed)
            paragraphs_text = [p["text"] for p in normalized.get("paragraphs", []) if p.get("text")]
            raw_text = "\n\n".join(paragraphs_text) if paragraphs_text else parser.extract_text(file_content)
            
            job.progress = 45.0
            await self.db.flush()

            # Stage 3: Perform Text Cleaning (45% -> 60%)
            cleaned_text = TextCleaner.clean_text(raw_text)
            job.progress = 60.0
            await self.db.flush()

            # Save / update DocumentContent table for raw extraction records
            stmt_content = select(DocumentContent).where(DocumentContent.document_id == document_id)
            content_rec = (await self.db.execute(stmt_content)).scalar_one_or_none()
            stats = normalized.get("statistics", {})
            if content_rec:
                content_rec.content_json = normalized
                content_rec.extracted_text = cleaned_text
                content_rec.statistics = stats
            else:
                content_rec = DocumentContent(
                    document_id=document_id,
                    content_json=normalized,
                    extracted_text=cleaned_text,
                    statistics=stats
                )
                self.db.add(content_rec)
            await self.db.flush()

            # Stage 4: Intelligent Semantic Chunking (60% -> 85%)
            chunker = SemanticChunker(target_chunk_tokens=600, overlap_tokens=125)
            chunks_data = chunker.chunk_document(
                cleaned_text=cleaned_text,
                document_id=document_id,
                organization_id=doc.organization_id,
                workspace_id=doc.workspace_id,
                sections=normalized.get("sections", [])
            )
            job.progress = 85.0
            await self.db.flush()

            # Stage 5: Delete existing chunks & Save new DocumentChunk records (85% -> 100%)
            await self.db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))

            for chunk_info in chunks_data:
                chunk_entity = DocumentChunk(
                    document_id=document_id,
                    organization_id=doc.organization_id,
                    workspace_id=doc.workspace_id,
                    chunk_index=chunk_info["chunk_index"],
                    page_number=chunk_info.get("page_number"),
                    section_title=chunk_info.get("section_title"),
                    content=chunk_info["content"],
                    token_count=chunk_info["token_count"],
                    character_count=chunk_info["character_count"],
                    checksum=chunk_info["checksum"],
                    metadata_json=chunk_info["metadata_json"]
                )
                self.db.add(chunk_entity)

            await self.db.flush()

            # Automatic Embedding Generation (Phase 3.3)
            try:
                from ..ai.embeddings.service import EmbeddingService
                emb_service = EmbeddingService(self.db)
                await emb_service.generate_document_embeddings(document_id, provider_name="gemini")
            except Exception as emb_err:
                logger.warning(f"Automatic embedding generation warning for document {document_id}: {emb_err}")

            # File Intelligence Analysis (Phase 2.5)
            try:
                from ..ai.extraction.file_analyzer import FileIntelligenceAnalyzer
                analyzer = FileIntelligenceAnalyzer(self.db)
                await analyzer.analyze_document(document_id)
            except Exception as intel_err:
                logger.warning(f"File Intelligence analysis warning for document {document_id}: {intel_err}")

            # Finish Job
            elapsed_ms = int((time.time() - start_time) * 1000)
            job.status = "COMPLETED"
            job.progress = 100.0
            job.completed_at = datetime.utcnow()
            job.processing_time_ms = elapsed_ms
            doc.processing_status = "COMPLETED"

            await self.db.flush()
            logger.info(f"Pipeline successfully completed for document: {document_id} ({len(chunks_data)} chunks, {elapsed_ms}ms)")
            return job

        except Exception as err:
            import traceback
            print("DEBUG process_document exception:", err)
            traceback.print_exc()
            job.retry_count += 1
            if job.retry_count < 3:
                job.status = "RETRYING"
                doc.processing_status = "RETRYING"
            else:
                job.status = "FAILED"
                doc.processing_status = "FAILED"

            job.error_message = str(err)
            job.completed_at = datetime.utcnow()
            await self.db.flush()
            return job
