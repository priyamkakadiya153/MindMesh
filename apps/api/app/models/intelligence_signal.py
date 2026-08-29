from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, ForeignKey, JSON
from uuid import UUID
from typing import Optional, Dict, Any
from .base import BaseEntity

class IntelligenceSignal(BaseEntity):
    __tablename__ = "intelligence_signals"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True)
    project_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    user_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    signal_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # NEW_DECISION, BLOCKED_TASK, OVERDUE_TASK, OPEN_QUESTION, KNOWLEDGE_CONFLICT, STALE_KNOWLEDGE, DECISION_AFFECTS_TASK, PROJECT_ATTENTION
    priority: Mapped[str] = mapped_column(String(20), default="NORMAL", nullable=False)  # LOW, NORMAL, HIGH
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", index=True, nullable=False)  # ACTIVE, READ, DISMISSED, RESOLVED

    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
