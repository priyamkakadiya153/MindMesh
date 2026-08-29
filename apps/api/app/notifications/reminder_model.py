from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, ForeignKey, Uuid, DateTime
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional
from ..models.base import BaseEntity

class Reminder(BaseEntity):
    __tablename__ = "reminders"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    organization_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    timezone: Mapped[str] = mapped_column(String(100), nullable=False, default="Asia/Kolkata")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="SCHEDULED", index=True)  # SCHEDULED, TRIGGERED, COMPLETED, CANCELLED, FAILED
    source_conversation_id: Mapped[Optional[UUID]] = mapped_column(Uuid, nullable=True)

    user: Mapped["User"] = relationship()
