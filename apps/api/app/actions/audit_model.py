import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseEntity

class ActionEvent(BaseEntity):
    """PostgreSQL model for authoritative, immutable Action Audit Trail."""

    __tablename__ = "action_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    actor_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    action_type = Column(String(64), nullable=False, index=True) # CREATE_TASK, SEND_DIRECT_MESSAGE, etc.
    status = Column(String(32), nullable=False, default="SUCCEEDED", index=True) # SUCCEEDED, FAILED, CANCELLED, EXPIRED
    source_type = Column(String(32), nullable=False, default="AI_CHAT", index=True) # AI_CHAT, DIRECT_UI, AUTOMATION, SYSTEM

    target_type = Column(String(32), nullable=True, index=True) # TASK, DIRECT_MESSAGE, SCHEDULED_AUTOMATION
    target_id = Column(String(128), nullable=True, index=True)

    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    conversation_id = Column(String(128), nullable=True)
    message_id = Column(String(128), nullable=True)

    reason = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
