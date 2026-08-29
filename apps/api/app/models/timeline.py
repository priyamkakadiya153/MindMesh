from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey, Boolean, JSON, DateTime, Index
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Dict, Any, List
from .base import BaseEntity

class TimelineEvent(BaseEntity):
    """Normalized representation of organizational knowledge timeline events.

    Captures when events occurred temporally, original source references, and

    importance levels without duplicating source data.

    """
    __tablename__ = "timeline_events"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=True)
    project_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), index=True, nullable=True)

    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # DOCUMENT_CREATED, DOCUMENT_UPDATED, FILE_SHARED, CONVERSATION_STARTED,
    # DECISION_MADE, TASK_CREATED, TASK_COMPLETED, IMPORTANT_FACT_DISCOVERED,
    # PROJECT_CREATED, PROJECT_UPDATED, MILESTONE, KNOWLEDGE_UPDATED

    importance: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM", index=True)
    # HIGH, MEDIUM, LOW

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    # document, file, message, conversation, project, task, decision, insight
    source_id: Mapped[UUID] = mapped_column(index=True, nullable=False)

    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("idx_timeline_org_workspace_time", "organization_id", "workspace_id", "occurred_at"),
        Index("idx_timeline_source_unique", "source_type", "source_id", "event_type", unique=False),
    )


class TimelineRelation(BaseEntity):
    """Establishes temporal and causal lineage relationships between timeline

    events.

    """
    __tablename__ = "timeline_relations"

    source_event_id: Mapped[UUID] = mapped_column(ForeignKey("timeline_events.id", ondelete="CASCADE"), index=True, nullable=False)
    target_event_id: Mapped[UUID] = mapped_column(ForeignKey("timeline_events.id", ondelete="CASCADE"), index=True, nullable=False)

    relation_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    # CAUSED, UPDATED, SUPERSEDES, RESULTED_IN, RELATED_TO, DERIVED_FROM

    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    source_event: Mapped["TimelineEvent"] = relationship("TimelineEvent", foreign_keys=[source_event_id])
    target_event: Mapped["TimelineEvent"] = relationship("TimelineEvent", foreign_keys=[target_event_id])
