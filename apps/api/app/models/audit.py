from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, JSON
from uuid import UUID
from typing import Optional
from .base import BaseEntity

class AuditLog(BaseEntity):
    __tablename__ = "audit_logs"

    action: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    organization_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
