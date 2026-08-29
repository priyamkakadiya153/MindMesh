from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey, Boolean, JSON, DateTime, Float, Index
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Dict, Any, List
from .base import BaseEntity

class IntelligentConversationSummary(BaseEntity):
    """Normalized representation of a structured summary generated for a conversation/chat."""
    __tablename__ = "intelligent_conversation_summaries"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=True)
    chat_id: Mapped[UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), index=True, nullable=False)

    summary_type: Mapped[str] = mapped_column(String(30), nullable=False, default="QUICK", index=True)
    # QUICK, DETAILED, ACTION

    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    topics: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    timeline_json: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    open_questions: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    blockers_json: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    risks_json: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)


class ConversationExtractedItem(BaseEntity):
    """Normalized representation of a decision, task, question, or blocker extracted from a conversation message."""
    __tablename__ = "conversation_extracted_items"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=True)
    chat_id: Mapped[UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), index=True, nullable=False)
    message_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)

    item_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    # DECISION, TASK, QUESTION, BLOCKER, COMMITMENT

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    assignee_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    due_date_str: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.9)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="AI_DETECTED", index=True)
    # AI_DETECTED, CONFIRMED, REJECTED

    promoted_entity_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    promoted_entity_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
