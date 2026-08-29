from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Text, Boolean, Integer, DateTime, JSON
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List
from .base import BaseEntity

class Attachment(BaseEntity):
    __tablename__ = "attachments"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=True)
    conversation_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=True)
    message_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("direct_messages.id", ondelete="SET NULL"), index=True, nullable=True)
    folder_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("folders.id", ondelete="SET NULL"), index=True, nullable=True)
    
    uploaded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False) # size in bytes
    checksum: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True) # SHA-256
    
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preview_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active") # active, archived, deleted
    processing_status: Mapped[str] = mapped_column(String(50), nullable=False, default="ready") # uploading, processing, indexed, failed, ready
    download_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    uploader: Mapped["User"] = relationship("User")
    folder: Mapped[Optional["Folder"]] = relationship("Folder")
    versions: Mapped[List["AttachmentVersion"]] = relationship(back_populates="attachment", cascade="all, delete-orphan")
    access_logs: Mapped[List["AttachmentAccessLog"]] = relationship(back_populates="attachment", cascade="all, delete-orphan")


class AttachmentVersion(BaseEntity):
    __tablename__ = "attachment_versions"

    attachment_id: Mapped[UUID] = mapped_column(ForeignKey("attachments.id", ondelete="CASCADE"), index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    attachment: Mapped["Attachment"] = relationship(back_populates="versions")


class AttachmentAccessLog(BaseEntity):
    __tablename__ = "attachment_access_logs"

    attachment_id: Mapped[UUID] = mapped_column(ForeignKey("attachments.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(30), nullable=False) # view, download, preview
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    accessed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    attachment: Mapped["Attachment"] = relationship(back_populates="access_logs")
    user: Mapped["User"] = relationship("User")
