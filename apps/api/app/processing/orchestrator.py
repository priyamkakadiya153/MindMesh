import time
import logging
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .pipeline import ProcessingPipeline
from .models import DocumentContent
from ..ocr.engine import OCREngine
from ..ocr.pipeline import OCRPipeline
from ..knowledge.service import KnowledgeService
from ..knowledge.models import ProcessingEvent
from ..documents.models import Document
from ..documents.exceptions import DocumentNotFoundException

logger = logging.getLogger(__name__)

class ProcessingOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pipeline = ProcessingPipeline(db)
        self.k_service = KnowledgeService(db)

    async def log_event(self, document_id: UUID, stage: str, start_time: float, status: str = "COMPLETED", error: str = None):
        duration = int((time.time() - start_time) * 1000)
        event = ProcessingEvent(
            document_id=document_id,
            stage=stage,
            worker="LocalOrchestratorWorker",
            duration_ms=duration,
            status=status,
            error=error
        )
        self.db.add(event)
        await self.db.flush()

    async def orchestrate(self, document_id: UUID) -> bool:
        logger.info(f"Starting orchestration pipeline flow for document: {document_id}")
        
        stmt = select(Document).where(Document.id == document_id)
        doc = (await self.db.execute(stmt)).scalar_one_or_none()
        if not doc:
            raise DocumentNotFoundException(str(document_id))

        try:
            # Stage 1: EXTRACTING
            start = time.time()
            doc.processing_status = "EXTRACTING"
            await self.db.commit()
            
            content_rec = await self.pipeline.process_document(document_id)
            await self.log_event(document_id, "EXTRACTING", start)
            
            # Stage 2: OCR
            start = time.time()
            doc.processing_status = "OCR"
            await self.db.commit()
            
            requires_ocr = OCREngine.requires_ocr(doc.mime_type, content_rec.extracted_text)
            if requires_ocr:
                # Retrieve file bytes
                from ..storage.factory import StorageProviderFactory
                storage = StorageProviderFactory.get_provider()
                file_bytes = await storage.download(doc.storage_path)
                
                ocr_text, ocr_conf = await OCRPipeline.process_image(file_bytes)
                
                # Merge OCR text into paragraphs
                content_rec.extracted_text = ocr_text
                content_rec.content_json["paragraphs"] = [{"text": p.strip()} for p in ocr_text.split("\n\n") if p.strip()]
                content_rec.content_json["statistics"]["character_count"] = len(ocr_text)
                content_rec.content_json["statistics"]["word_count"] = len(ocr_text.split())
                
                await self.log_event(document_id, "OCR", start, metadata={"confidence": ocr_conf})
            else:
                await self.log_event(document_id, "OCR", start, status="SKIPPED")

            # Stage 3: NORMALIZING & ENRICHING
            start = time.time()
            doc.processing_status = "NORMALIZING"
            await self.db.commit()
            
            # Enrich and save knowledge
            await self.k_service.save_knowledge(document_id, content_rec.content_json)
            await self.log_event(document_id, "ENRICHING", start)

            # Mark as READY
            doc.processing_status = "READY"
            await self.db.commit()
            return True
            
        except Exception as e:
            logger.exception(f"Orchestration failure on document {document_id}")
            doc.processing_status = "FAILED"
            await self.log_event(document_id, "FAILED", time.time(), status="FAILED", error=str(e))
            await self.db.commit()
            raise e
