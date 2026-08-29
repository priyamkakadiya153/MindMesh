from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, JSON, String, Integer, Text, Boolean
from uuid import UUID
from typing import Optional, List
from .base import BaseEntity

class ConversationSummary(BaseEntity):
    __tablename__ = "conversation_summaries"
    __table_args__ = {'extend_existing': True}

    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    message_range_start: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    message_range_end: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    key_decisions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    action_items: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    topics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

class ConversationMemory(BaseEntity):
    __tablename__ = "conversation_memories"
    __table_args__ = {'extend_existing': True}

    chat_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), index=True, nullable=True)
    conversation_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), index=True, nullable=True)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True)
    organization_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    project_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    context_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    memory_type: Mapped[str] = mapped_column(String(50), nullable=False, default="fact")
    importance: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expiration_status: Mapped[str] = mapped_column(String(20), nullable=False, default="permanent")

    chat: Mapped[Optional["Chat"]] = relationship("Chat", foreign_keys=[chat_id])
    workspace: Mapped[Optional["Workspace"]] = relationship()
    project: Mapped[Optional["Project"]] = relationship()
