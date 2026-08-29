import asyncio
import logging
from datetime import datetime
from uuid import UUID
from typing import Optional
from sqlalchemy import select

from ..core.database import AsyncSessionLocal
from ..documents.models import Document, DocumentUploadJob
from ..documents.enums import ProcessingStatus
from .pipeline import ProcessingPipeline

logger = logging.getLogger(__name__)

async def process_document_job(document_id: UUID, upload_job_id: Optional[UUID] = None):
    """Background task to process document text extraction & intelligent chunking."""
    logger.info(f"Starting background extraction & chunking for document: {document_id}")
    
    async with AsyncSessionLocal() as session:
        try:
            pipeline = ProcessingPipeline(session)
            proc_job = await pipeline.process_document(document_id)
            
            # Also update legacy UploadJob if present
            if upload_job_id:
                stmt_job = select(DocumentUploadJob).where(DocumentUploadJob.id == upload_job_id)
                job = (await session.execute(stmt_job)).scalar_one_or_none()
                if job:
                    job.status = proc_job.status
                    job.finished_at = proc_job.completed_at
                    job.error_message = proc_job.error_message
                    await session.commit()

            logger.info(f"Successfully finished background processing job for document: {document_id}")
        except Exception as e:
            logger.exception(f"Background processing failed for document {document_id}: {e}")
