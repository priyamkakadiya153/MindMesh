from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, ForeignKey
from uuid import UUID
from typing import Optional
from .base import BaseEntity

class Citation(BaseEntity):
    __tablename__ = "citations"
    __table_args__ = {'extend_existing': True}

    message_id: Mapped[UUID] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), index=True, nullable=False)
    conversation_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), index=True, nullable=True)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    chunk_id: Mapped[UUID] = mapped_column(ForeignKey("document_chunks.id", ondelete="CASCADE"), index=True, nullable=False)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_score: Mapped[str] = mapped_column(String(20), nullable=False, default="High")
    citation_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    citation_tag: Mapped[str] = mapped_column(String(10), nullable=False, default="[1]")

    message: Mapped[Optional["Message"]] = relationship(back_populates="citations")
    document: Mapped[Optional["Document"]] = relationship()
