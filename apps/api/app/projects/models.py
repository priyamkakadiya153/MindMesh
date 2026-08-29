from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime
from uuid import UUID
from typing import List, Optional
from datetime import datetime
from ..models.base import BaseEntity

class Project(BaseEntity):
    __tablename__ = "projects"

    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    owner_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(20), default="#3B82F6", nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="private")
    status: Mapped[str] = mapped_column(String(20), index=True, nullable=False, default="active")
    default_ai_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    workspace: Mapped["Workspace"] = relationship(back_populates="projects")
    organization: Mapped["Organization"] = relationship()
    owner: Mapped[Optional["User"]] = relationship(foreign_keys=[owner_id])
    members: Mapped[List["ProjectMember"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    settings: Mapped[Optional["ProjectSettings"]] = relationship(back_populates="project", uselist=False, cascade="all, delete-orphan")
    documents: Mapped[List["Document"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    tasks: Mapped[List["Task"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class ProjectMember(BaseEntity):
    __tablename__ = "project_members"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="viewer")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship()


class ProjectSettings(BaseEntity):
    __tablename__ = "project_settings"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), unique=True, nullable=False)
    allow_external_sharing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    default_view: Mapped[str] = mapped_column(String(50), default="overview", nullable=False)
    enable_ai: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notification_level: Mapped[str] = mapped_column(String(50), default="all", nullable=False)

    project: Mapped["Project"] = relationship(back_populates="settings")
