from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, DateTime
from uuid import UUID
from datetime import datetime
from typing import Optional
from ..models.base import BaseEntity

class VectorIndex(BaseEntity):
    __tablename__ = "vector_indexes"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    similarity_metric: Mapped[str] = mapped_column(String(50), nullable=False, default="COSINE")
    index_type: Mapped[str] = mapped_column(String(50), nullable=False, default="HNSW")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")

    organization: Mapped["Organization"] = relationship()

class EmbeddingJob(BaseEntity):
    __tablename__ = "embedding_jobs"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    operation: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., GENERATE, REBUILD, DELETE, SYNC
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="QUEUED") # e.g., QUEUED, PROCESSING, COMPLETED, FAILED
    worker: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    document: Mapped["Document"] = relationship()
