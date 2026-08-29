from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime
from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional
import secrets
from .base import BaseEntity

class Invitation(BaseEntity):
    __tablename__ = "invitations"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True)
    project_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    mobile: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    invited_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False) # pending, accepted, rejected, expired, cancelled
    expires_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=7), nullable=False)

    organization: Mapped["Organization"] = relationship()
    workspace: Mapped[Optional["Workspace"]] = relationship()
    project: Mapped[Optional["Project"]] = relationship()
    inviter: Mapped[Optional["User"]] = relationship(foreign_keys=[invited_by])

    @classmethod
    def generate_token(cls) -> str:
        return secrets.token_urlsafe(32)
