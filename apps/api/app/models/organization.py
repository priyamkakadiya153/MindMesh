from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Text, Boolean, DateTime
from uuid import UUID
from typing import List, Optional
from datetime import datetime
from .base import BaseEntity

class Organization(BaseEntity):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    owner_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    visibility: Mapped[str] = mapped_column(String(50), default="private", nullable=False)
    is_personal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    owner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_id])
    members: Mapped[List["OrganizationMember"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    workspaces: Mapped[List["Workspace"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    settings: Mapped[Optional["OrganizationSettings"]] = relationship(back_populates="organization", uselist=False, cascade="all, delete-orphan")
    invitations: Mapped[List["OrganizationInvitation"]] = relationship(back_populates="organization", cascade="all, delete-orphan")


class OrganizationSettings(BaseEntity):
    __tablename__ = "organization_settings"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=False)
    default_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    theme: Mapped[str] = mapped_column(String(20), default="dark", nullable=False)
    branding_color: Mapped[str] = mapped_column(String(20), default="#3B82F6", nullable=False)
    allow_public_invites: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_guest_access: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="settings")


class OrganizationInvitation(BaseEntity):
    __tablename__ = "organization_invitations"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    invited_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="invitations")
    inviter: Mapped[Optional["User"]] = relationship(foreign_keys=[invited_by])


