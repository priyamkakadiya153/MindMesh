from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from .repository import KnowledgeRepository
from .enrichment import EnrichmentService

class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = KnowledgeRepository(db)

    async def get_knowledge(self, document_id: UUID):
        return await self.repo.get_entry_by_doc_id(document_id)

    async def get_statistics(self, document_id: UUID):
        return await self.repo.get_statistics_by_doc_id(document_id)

    async def save_knowledge(self, document_id: UUID, normalized_content: dict):
        # 1. Enrich parsed outputs
        enriched = EnrichmentService.enrich_document_content(normalized_content)
        
        # 2. Save KnowledgeEntry
        entry = await self.repo.save_knowledge_entry(
            document_id=document_id,
            extracted_text=enriched["extracted_text"],
            normalized_content=normalized_content,
            language=enriched["language"],
            summary=enriched["summary"],
            keywords=enriched["keywords"],
            topics=enriched["topics"],
            quality_score=enriched["quality_score"],
            processing_state="READY"
        )
        
        # 3. Save Document Statistics
        await self.repo.save_statistics(document_id, enriched["statistics"])
        
        return entry
