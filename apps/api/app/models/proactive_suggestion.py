from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Float, DateTime, Text, ForeignKey
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

from ..database.base import Base
from .base import BaseEntity

class ProactiveSuggestion(BaseEntity):
    """
    AUTO-08 Candidate Action / Deadline Proactive Suggestion Model.
    Stores detected actionable commitments, deadlines, and follow-ups.
    """
    __tablename__ = "proactive_suggestions"

    organization_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    user_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)

    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="DIRECT_MESSAGE")
    conversation_id: Mapped[str] = mapped_column(String(100), nullable=False)
    message_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    detected_action_type: Mapped[str] = mapped_column(String(50), nullable=False, default="TASK") # TASK or REMINDER
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deadline: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # Human display deadline e.g. "Friday"
    normalized_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    assignee_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    assignee_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    confidence: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    confidence_level: Mapped[str] = mapped_column(String(20), default="HIGH", nullable=False) # HIGH, MEDIUM, LOW

    status: Mapped[str] = mapped_column(String(50), default="DETECTED", nullable=False) # DETECTED, PENDING_CONFIRMATION, SHOWN, DISMISSED, ACCEPTED, RESOLVED, EXPIRED, CANCELLED
    detected_action_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    source_label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # e.g. "Direct Message with Dhruvil"
    source_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Original message snippet

    pending_target_action_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # CREATE_TASK or CREATE_REMINDER
    pending_proposal_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Serialized JSON payload of pending proposal

    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    executed_action_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)

    agent_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    agent_execution_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    agent_output_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)

