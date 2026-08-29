from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime, JSON
from uuid import UUID
from typing import Optional, Dict, Any
from datetime import datetime
from .base import BaseEntity

class KnowledgeGovernance(BaseEntity):
    __tablename__ = "knowledge_governance"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True)
    project_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)

    entity_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # DOCUMENT, DECISION, TASK, PROJECT
    entity_id: Mapped[UUID] = mapped_column(index=True, nullable=False)

    lifecycle_state: Mapped[str] = mapped_column(String(30), default="ACTIVE", index=True, nullable=False)  # ACTIVE, SUPERSEDED, ARCHIVED
    verification_state: Mapped[str] = mapped_column(String(30), default="UNVERIFIED", index=True, nullable=False)  # UNVERIFIED, SUPPORTED, VERIFIED, CONFLICTING
    authority_state: Mapped[str] = mapped_column(String(30), default="NORMAL", nullable=False)  # AUTHORITATIVE, NORMAL, REFERENCE

    verified_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    superseded_by: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    review_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class GovernanceAuditLog(BaseEntity):
    __tablename__ = "governance_audit_logs"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # VERIFY, UNVERIFY, SUPERSEDE, ARCHIVE, RESTORE
    previous_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_state: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
