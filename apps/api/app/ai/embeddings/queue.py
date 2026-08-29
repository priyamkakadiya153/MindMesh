import logging
from uuid import UUID
from fastapi import BackgroundTasks
from ...core.database import AsyncSessionLocal
from .service import EmbeddingService

logger = logging.getLogger(__name__)

async def process_embeddings_job(document_id: UUID):
    """Background task worker to run chunking and embedding generation."""
    logger.info(f"Starting background embeddings generation for document: {document_id}")
    async with AsyncSessionLocal() as session:
        try:
            service = EmbeddingService(session)
            num_chunks = await service.generate_document_embeddings(document_id)
            logger.info(f"Completed embeddings generation: {num_chunks} chunks indexed for document {document_id}")
        except Exception as e:
            logger.exception(f"Embeddings background task failed for document: {document_id}")

class EmbeddingsQueue:
    @staticmethod
    def enqueue(background_tasks: BackgroundTasks, document_id: UUID):
        """Helper to enqueue embeddings generation job into BackgroundTasks."""
        logger.info(f"Enqueuing embedding generation job for document: {document_id}")
        background_tasks.add_task(process_embeddings_job, document_id)
