from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime
from uuid import UUID
from typing import Optional
from datetime import datetime
from .base import BaseEntity

class OrganizationMember(BaseEntity):
    __tablename__ = "organization_members"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False)
    role_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("roles.id", ondelete="SET NULL"), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="memberships")
    role_rel: Mapped[Optional["Role"]] = relationship("Role", foreign_keys=[role_id])

