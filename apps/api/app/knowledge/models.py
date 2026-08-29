from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, ForeignKey, Text, JSON, DateTime, Boolean
from uuid import UUID
from datetime import datetime
from ..models.base import BaseEntity

class KnowledgeEntry(BaseEntity):
    __tablename__ = "knowledge_entries"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False, unique=True)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_content: Mapped[dict] = mapped_column(JSON, nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False, default="en")
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    keywords: Mapped[dict] = mapped_column(JSON, nullable=True)
    topics: Mapped[dict] = mapped_column(JSON, nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    processing_state: Mapped[str] = mapped_column(String(50), nullable=False, default="UPLOADED")

    document: Mapped["Document"] = relationship()

class ProcessingEvent(BaseEntity):
    __tablename__ = "processing_events"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    worker: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    error: Mapped[str] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    document: Mapped["Document"] = relationship()

class DocumentStatistic(BaseEntity):
    __tablename__ = "document_statistics"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True, index=True, nullable=False)
    pages: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    words: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    characters: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    paragraphs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tables: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    images: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    headings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reading_time: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    document: Mapped["Document"] = relationship()
