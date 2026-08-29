from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey
from uuid import UUID
from typing import Optional
from .base import BaseEntity

class JoinRequest(BaseEntity):
    __tablename__ = "join_requests"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True)
    project_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False) # pending, approved, rejected, cancelled

    organization: Mapped["Organization"] = relationship()
    workspace: Mapped[Optional["Workspace"]] = relationship()
    project: Mapped[Optional["Project"]] = relationship()
    user: Mapped["User"] = relationship()
