from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime
from uuid import UUID
from typing import List, Optional
from datetime import datetime
from ..models.base import BaseEntity

class Workspace(BaseEntity):
    __tablename__ = "workspaces"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(20), default="#3B82F6", nullable=True)
    owner_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="workspaces")
    owner: Mapped[Optional["User"]] = relationship(foreign_keys=[owner_id])
    projects: Mapped[List["Project"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    members: Mapped[List["WorkspaceMember"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    documents: Mapped[List["Document"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    settings: Mapped[Optional["WorkspaceSettings"]] = relationship(back_populates="workspace", uselist=False, cascade="all, delete-orphan")
    creator: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by])

class WorkspaceMember(BaseEntity):
    __tablename__ = "workspace_members"

    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="member")
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    workspace: Mapped["Workspace"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship()


class WorkspaceSettings(BaseEntity):
    __tablename__ = "workspace_settings"

    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), unique=True, nullable=False)
    theme: Mapped[str] = mapped_column(String(20), default="dark", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    default_dashboard: Mapped[str] = mapped_column(String(50), default="overview", nullable=False)
    allow_ai: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    visibility: Mapped[str] = mapped_column(String(20), default="private", nullable=False)
    default_ai_model: Mapped[str] = mapped_column(String(50), default="gemini-2.5-flash", nullable=False)
    auto_index_files: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_semantic_search: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_ai_chat: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    workspace: Mapped["Workspace"] = relationship(back_populates="settings")

