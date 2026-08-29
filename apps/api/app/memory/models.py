from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, JSON, Float, Boolean, DateTime, Integer
from uuid import UUID
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.base import BaseEntity

class LongTermMemory(BaseEntity):
    __tablename__ = "long_term_memories"

    memory_type: Mapped[str] = mapped_column(String, index=True, nullable=False)  # User, Project, Organization, Agent
    scope_key: Mapped[str] = mapped_column(String, index=True, nullable=False)  # user_id or project_id or agent_id
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)
    project_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    
    key: Mapped[str] = mapped_column(String, index=True, nullable=False)  # e.g., preferred_language
    value: Mapped[dict] = mapped_column(JSON, nullable=False)  # holds memory data payload
    importance_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    
    retention_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_accessed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

class AgentFeedback(BaseEntity):
    __tablename__ = "agent_feedback"

    execution_id: Mapped[Optional[UUID]] = mapped_column(index=True, nullable=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    
    feedback_type: Mapped[str] = mapped_column(String, nullable=False)  # explicit_like, dislike, manual_edit
    rating: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # scale 1-5 or -1/+1
    comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    context_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

class GovernancePolicy(BaseEntity):
    __tablename__ = "governance_policies"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, index=True, nullable=False)  # Security, Data, Memory, Workflow, Tool, Compliance, Privacy
    rules: Mapped[dict] = mapped_column(JSON, nullable=False)  # Rule structures dictionary
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

class AuditDecisionLog(BaseEntity):
    __tablename__ = "audit_decision_logs"

    execution_id: Mapped[UUID] = mapped_column(index=True, nullable=False)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    selected_tools: Mapped[dict] = mapped_column(JSON, nullable=False)  # list of tools
    retrieved_documents: Mapped[dict] = mapped_column(JSON, nullable=False)  # list of doc references
    applied_policies: Mapped[dict] = mapped_column(JSON, nullable=False)  # list of policy checks
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    trust_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    execution_summary: Mapped[Optional[str]] = mapped_column(String, nullable=True)
