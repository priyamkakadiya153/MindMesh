from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, BigInteger, Float, ForeignKey, DateTime, Text, Boolean, JSON
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from ..models.base import BaseEntity

class Folder(BaseEntity):
    __tablename__ = "folders"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    parent_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("folders.id", ondelete="CASCADE"), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    parent: Mapped[Optional["Folder"]] = relationship("Folder", remote_side="Folder.id", backref="children")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="folder")

class Document(BaseEntity):
    __tablename__ = "documents"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    project_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=True)
    uploaded_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    folder_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("folders.id", ondelete="SET NULL"), index=True, nullable=True)

    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    extension: Mapped[str] = mapped_column(String(20), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="local")
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    processing_status: Mapped[str] = mapped_column(String(50), nullable=False, default="QUEUED")
    visibility: Mapped[str] = mapped_column(String(50), nullable=False, default="private")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    workspace: Mapped["Workspace"] = relationship(back_populates="documents")
    project: Mapped[Optional["Project"]] = relationship(back_populates="documents")
    folder: Mapped[Optional["Folder"]] = relationship(back_populates="documents")
    upload_jobs: Mapped[list["DocumentUploadJob"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    processing_jobs: Mapped[list["DocumentProcessingJob"]] = relationship(back_populates="document", cascade="all, delete-orphan")

    doc_metadata: Mapped[Optional["DocumentMetadata"]] = relationship(back_populates="document", cascade="all, delete-orphan", uselist=False)
    intelligence: Mapped[Optional["FileIntelligence"]] = relationship(back_populates="document", cascade="all, delete-orphan", uselist=False)
    versions: Mapped[list["DocumentVersion"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    audit_logs: Mapped[list["DocumentAuditLog"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    favorites: Mapped[list["DocumentFavorite"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    shares: Mapped[list["DocumentShare"]] = relationship(back_populates="document", cascade="all, delete-orphan")

    @property
    def owner_id(self) -> Optional[UUID]:
        return self.uploaded_by

    @property
    def size_bytes(self) -> int:
        return self.size

    @property
    def checksum(self) -> str:
        return self.checksum_sha256

    @property
    def status(self) -> str:
        return self.processing_status

class FileIntelligence(BaseEntity):
    __tablename__ = "file_intelligences"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False, unique=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    project_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=True)

    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    topics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    keywords: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    entities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    facts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    decisions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    tasks: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)

    language: Mapped[str] = mapped_column(String(50), nullable=False, default="en")
    document_type: Mapped[str] = mapped_column(String(100), nullable=False, default="Unknown")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="UPLOADED") # UPLOADED, EXTRACTING, INDEXING, ANALYZING, COMPLETED, PARTIAL, FAILED
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="intelligence")

class DocumentFavorite(BaseEntity):
    __tablename__ = "document_favorites"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    document: Mapped["Document"] = relationship(back_populates="favorites")

class DocumentShare(BaseEntity):
    __tablename__ = "document_shares"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    shared_with_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    permission_level: Mapped[str] = mapped_column(String(50), nullable=False, default="read") # read, write, admin
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    document: Mapped["Document"] = relationship(back_populates="shares")

class DocumentUploadJob(BaseEntity):
    __tablename__ = "document_upload_jobs"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="QUEUED")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="upload_jobs")

class DocumentProcessingJob(BaseEntity):
    __tablename__ = "document_processing_jobs"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="QUEUED") # QUEUED, PROCESSING, COMPLETED, FAILED, RETRYING
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processing_time_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    document: Mapped["Document"] = relationship(back_populates="processing_jobs")

class DocumentMetadata(BaseEntity):
    __tablename__ = "document_metadata"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="en")
    keywords: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    labels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    categories: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    business_unit: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confidentiality: Mapped[str] = mapped_column(String(50), nullable=False, default="internal")
    custom_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="doc_metadata")

class DocumentVersion(BaseEntity):
    __tablename__ = "document_versions"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    change_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="versions")

class DocumentAuditLog(BaseEntity):
    __tablename__ = "document_audit_logs"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    action_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    document: Mapped["Document"] = relationship(back_populates="audit_logs")


class RetentionPolicy(BaseEntity):
    __tablename__ = "retention_policies"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False)
    auto_archive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_delete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


