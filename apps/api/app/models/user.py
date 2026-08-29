from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, ForeignKey, DateTime
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from .base import BaseEntity

class User(BaseEntity):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, default="", nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    firebase_uid: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    timezone: Mapped[str] = mapped_column(String, default="UTC", nullable=False)
    language: Mapped[str] = mapped_column(String, default="en", nullable=False)
    theme: Mapped[str] = mapped_column(String, default="dark", nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    current_organization_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    current_workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)

    memberships: Mapped[List["OrganizationMember"]] = relationship(back_populates="user", cascade="all, delete-orphan", foreign_keys="[OrganizationMember.user_id]")
    current_organization: Mapped[Optional["Organization"]] = relationship("Organization", foreign_keys=[current_organization_id])
    current_workspace: Mapped[Optional["Workspace"]] = relationship("Workspace", foreign_keys=[current_workspace_id])

    @property
    def organization_id(self) -> Optional[UUID]:
        return self.current_organization_id

    @property
    def display_name(self) -> Optional[str]:
        if self.first_name or self.last_name:
            return f"{self.first_name or ''} {self.last_name or ''}".strip()
        return None

    @property
    def full_name(self) -> str:
        if self.first_name or self.last_name:
            return f"{self.first_name or ''} {self.last_name or ''}".strip()
        return self.username or self.email

    @property
    def mobile(self) -> Optional[str]:
        return self.phone_number

    @mobile.setter
    def mobile(self, value: Optional[str]):
        self.phone_number = value



