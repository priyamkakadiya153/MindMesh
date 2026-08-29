from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import KnowledgeEntry, DocumentStatistic

class KnowledgeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_entry_by_doc_id(self, document_id: UUID) -> KnowledgeEntry:
        stmt = select(KnowledgeEntry).where(KnowledgeEntry.document_id == document_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_statistics_by_doc_id(self, document_id: UUID) -> DocumentStatistic:
        stmt = select(DocumentStatistic).where(DocumentStatistic.document_id == document_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save_knowledge_entry(
        self,
        document_id: UUID,
        extracted_text: str,
        normalized_content: dict,
        language: str,
        summary: str,
        keywords: list[str],
        topics: list[str],
        quality_score: float,
        processing_state: str = "READY"
    ) -> KnowledgeEntry:
        entry = await self.get_entry_by_doc_id(document_id)
        if entry:
            entry.extracted_text = extracted_text
            entry.normalized_content = normalized_content
            entry.language = language
            entry.summary = summary
            entry.keywords = {"keywords": keywords}
            entry.topics = {"topics": topics}
            entry.quality_score = quality_score
            entry.processing_state = processing_state
        else:
            entry = KnowledgeEntry(
                document_id=document_id,
                extracted_text=extracted_text,
                normalized_content=normalized_content,
                language=language,
                summary=summary,
                keywords={"keywords": keywords},
                topics={"topics": topics},
                quality_score=quality_score,
                processing_state=processing_state
            )
            self.db.add(entry)
            
        await self.db.flush()
        return entry

    async def save_statistics(
        self,
        document_id: UUID,
        stats_data: dict
    ) -> DocumentStatistic:
        stats = await self.get_statistics_by_doc_id(document_id)
        if stats:
            stats.pages = stats_data.get("pages", 1)
            stats.words = stats_data.get("words", 0)
            stats.characters = stats_data.get("characters", 0)
            stats.paragraphs = stats_data.get("paragraphs", 0)
            stats.tables = stats_data.get("tables", 0)
            stats.images = stats_data.get("images", 0)
            stats.headings = stats_data.get("headings", 0)
            stats.reading_time = stats_data.get("reading_time", 0)
        else:
            stats = DocumentStatistic(
                document_id=document_id,
                pages=stats_data.get("pages", 1),
                words=stats_data.get("words", 0),
                characters=stats_data.get("characters", 0),
                paragraphs=stats_data.get("paragraphs", 0),
                tables=stats_data.get("tables", 0),
                images=stats_data.get("images", 0),
                headings=stats_data.get("headings", 0),
                reading_time=stats_data.get("reading_time", 0)
            )
            self.db.add(stats)
            
        await self.db.flush()
        return stats
