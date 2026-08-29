from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Text, JSON
from uuid import UUID
from typing import Optional
from ...models.base import BaseEntity

class DocumentChunk(BaseEntity):
    __tablename__ = "document_chunks"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    character_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    document: Mapped["Document"] = relationship()
    embedding: Mapped[Optional["DocumentEmbedding"]] = relationship(back_populates="chunk", cascade="all, delete-orphan", uselist=False, foreign_keys="[DocumentEmbedding.chunk_id]")

class DocumentEmbedding(BaseEntity):
    __tablename__ = "document_embeddings"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    chunk_id: Mapped[UUID] = mapped_column(ForeignKey("document_chunks.id", ondelete="CASCADE"), index=True, nullable=False, unique=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    embedding_dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    vector_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=True)
    embedding: Mapped[list[float]] = mapped_column(JSON, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, default="")

    chunk: Mapped["DocumentChunk"] = relationship(back_populates="embedding", foreign_keys=[chunk_id])
