from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey, DateTime, JSON
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.base import BaseEntity

class ScheduledAutomation(BaseEntity):
    __tablename__ = "scheduled_automations"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="SET NULL"), index=True, nullable=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # CREATE_REMINDER, SEND_DIRECT_MESSAGE, CREATE_TASK
    action_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False) # Structured parameters

    schedule_type: Mapped[str] = mapped_column(String(30), nullable=False) # ONE_TIME, DAILY, WEEKLY, WEEKDAYS, MONTHLY
    recurrence_rule: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="Asia/Kolkata")

    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True, nullable=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE", index=True) # ACTIVE, PAUSED, COMPLETED, CANCELLED
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_run_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True) # SUCCESS, FAILED

    source_conversation_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    executions: Mapped[List["AutomationExecutionRecord"]] = relationship(back_populates="automation", cascade="all, delete-orphan")


class AutomationExecutionRecord(BaseEntity):
    __tablename__ = "automation_execution_records"

    automation_id: Mapped[UUID] = mapped_column(ForeignKey("scheduled_automations.id", ondelete="CASCADE"), index=True, nullable=False)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="SUCCESS") # SUCCESS, FAILED, SKIPPED
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    automation: Mapped["ScheduledAutomation"] = relationship(back_populates="executions")
