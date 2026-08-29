from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, Boolean
from uuid import UUID
from datetime import datetime
from typing import Optional
from .base import BaseEntity

class Task(BaseEntity):
    __tablename__ = "tasks"

    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="TODO", nullable=False)  # TODO, IN_PROGRESS, BLOCKED, COMPLETED, CANCELLED
    task_type: Mapped[str] = mapped_column(String, default="TASK", nullable=False)  # TASK, ACTION_ITEM, FOLLOW_UP
    priority: Mapped[str] = mapped_column(String, default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, URGENT

    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    assignee_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True)
    project_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)

    # Provenance fields
    source_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # CONVERSATION, DOCUMENT, DECISION, USER_CREATED
    source_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    decision_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("conversation_memories.id", ondelete="SET NULL"), nullable=True)
    conversation_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    message_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("direct_messages.id", ondelete="SET NULL"), nullable=True)
    document_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)

    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_ai_extracted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    blocked_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="tasks")
