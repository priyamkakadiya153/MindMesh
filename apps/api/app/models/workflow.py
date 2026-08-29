from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey, Boolean, JSON, DateTime, Integer, Index
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Dict, Any, List
from .base import BaseEntity

class AgenticWorkflow(BaseEntity):
    """Normalized representation of a goal-driven multi-step agentic workflow."""
    __tablename__ = "agentic_workflows"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=True)
    project_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), index=True, nullable=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    goal: Mapped[str] = mapped_column(String(255), nullable=False)
    workflow_type: Mapped[str] = mapped_column(String(50), nullable=False, default="CUSTOM")
    # PROJECT_RELEASE_READINESS, PROJECT_HANDOFF, KNOWLEDGE_CLEANUP, DOCUMENTATION_COMPLETION, CUSTOM

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT", index=True)
    # DRAFT, WAITING_FOR_APPROVAL, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED

    context_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    steps: Mapped[List["WorkflowStep"]] = relationship(
        "WorkflowStep",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowStep.step_index"
    )


class WorkflowStep(BaseEntity):
    """Normalized representation of an individual step within an AgenticWorkflow."""
    __tablename__ = "workflow_steps"

    workflow_id: Mapped[UUID] = mapped_column(ForeignKey("agentic_workflows.id", ondelete="CASCADE"), index=True, nullable=False)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)

    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # CREATE_TASK, UPDATE_TASK, VERIFY_KNOWLEDGE, RESOLVE_CONFLICT, CREATE_DRAFT, USER_DECISION

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    source_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)

    expected_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING", index=True)
    # PENDING, READY, RUNNING, COMPLETED, FAILED, SKIPPED, BLOCKED

    dependency_step_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workflow_steps.id", ondelete="SET NULL"), nullable=True)
    result_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    workflow: Mapped["AgenticWorkflow"] = relationship("AgenticWorkflow", back_populates="steps")
