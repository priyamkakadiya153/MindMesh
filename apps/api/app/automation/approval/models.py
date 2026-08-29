from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime, JSON, Integer
from uuid import UUID, uuid4
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.models.base import BaseEntity

class WorkflowDefinition(BaseEntity):
    __tablename__ = "workflows"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    definition: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)  # JSON structure containing steps
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)

    executions: Mapped[List["WorkflowExecution"]] = relationship(back_populates="workflow", cascade="all, delete-orphan")
    schedules: Mapped[List["WorkflowSchedule"]] = relationship(back_populates="workflow", cascade="all, delete-orphan")

class WorkflowExecution(BaseEntity):
    __tablename__ = "workflow_executions"

    workflow_id: Mapped[UUID] = mapped_column(ForeignKey("workflows.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Draft", nullable=False)  # Draft, Running, Waiting, Completed, Failed, Cancelled, Rolled Back
    context: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)  # stores run context variables/results
    current_step_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)

    workflow: Mapped["WorkflowDefinition"] = relationship(back_populates="executions")
    step_executions: Mapped[List["WorkflowStepExecution"]] = relationship(back_populates="execution", cascade="all, delete-orphan")
    approvals: Mapped[List["ApprovalRequest"]] = relationship(back_populates="execution", cascade="all, delete-orphan")

class WorkflowStepExecution(BaseEntity):
    __tablename__ = "workflow_step_executions"

    execution_id: Mapped[UUID] = mapped_column(ForeignKey("workflow_executions.id", ondelete="CASCADE"), index=True, nullable=False)
    step_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Pending", nullable=False)  # Pending, Running, Completed, Failed, Skipped, Rolled Back
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[float]] = mapped_column(nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    execution: Mapped["WorkflowExecution"] = relationship(back_populates="step_executions")

class ApprovalRequest(BaseEntity):
    __tablename__ = "workflow_approvals"

    workflow_execution_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workflow_executions.id", ondelete="CASCADE"), index=True, nullable=True)
    step_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Waiting", nullable=False)  # Waiting, Approved, Rejected, Escalated, Delegated
    assigned_approver: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # User ID or role/department name
    policy_type: Mapped[str] = mapped_column(String(50), default="Single", nullable=False)  # Single, Multi, Majority, Department, Executive
    approvers_voted: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)  # e.g., {"user_id": "Approved"}
    decision_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    decision_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    escalated_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    delegated_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sla_limit_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)

    execution: Mapped[Optional["WorkflowExecution"]] = relationship(back_populates="approvals")

class WorkflowSchedule(BaseEntity):
    __tablename__ = "workflow_schedules"

    workflow_id: Mapped[UUID] = mapped_column(ForeignKey("workflows.id", ondelete="CASCADE"), index=True, nullable=False)
    schedule_type: Mapped[str] = mapped_column(String(50), nullable=False)  # cron, interval, one-time
    expression: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. cron string or seconds interval
    next_run_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)

    workflow: Mapped["WorkflowDefinition"] = relationship(back_populates="schedules")

class AutomationEventLog(BaseEntity):
    __tablename__ = "automation_events"

    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    triggered_workflow_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workflow_executions.id", ondelete="SET NULL"), nullable=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)
