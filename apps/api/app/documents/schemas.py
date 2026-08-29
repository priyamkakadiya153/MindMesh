from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Union, Dict, Any
from .enums import ProcessingStatus, DocumentVisibility

class DocumentResponse(BaseModel):
    id: UUID
    organization_id: UUID
    workspace_id: UUID
    project_id: Optional[UUID] = None
    folder_id: Optional[UUID] = None
    uploaded_by: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    title: Optional[str] = None
    filename: str
    original_filename: str
    stored_filename: Optional[str] = None
    mime_type: str
    extension: str
    size: int
    size_bytes: Optional[int] = None
    checksum_sha256: str
    checksum: Optional[str] = None
    storage_provider: str
    storage_path: str
    processing_status: str
    status: Optional[str] = None
    visibility: str
    version: int
    deleted_at: Optional[datetime] = None
    is_favorite: Optional[bool] = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentListItem(BaseModel):
    id: UUID
    organization_id: Optional[UUID] = None
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    folder_id: Optional[UUID] = None
    title: Optional[str] = None
    filename: str
    original_filename: Optional[str] = None
    mime_type: str
    extension: str
    size: int
    size_bytes: Optional[int] = None
    checksum_sha256: Optional[str] = None
    processing_status: str
    status: Optional[str] = None
    visibility: str = "private"
    version: int = 1
    deleted_at: Optional[datetime] = None
    is_favorite: Optional[bool] = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    folder_id: Optional[UUID] = None
    visibility: Optional[str] = None
    project_id: Optional[UUID] = None

class DocumentShareRequest(BaseModel):
    shared_with_user_id: UUID
    permission_level: str = "read" # read, write, admin

class FolderResponse(BaseModel):
    id: UUID
    organization_id: UUID
    workspace_id: UUID
    parent_id: Optional[UUID] = None
    name: str
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FolderCreate(BaseModel):
    workspace_id: UUID
    name: str
    parent_id: Optional[UUID] = None

class FolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[UUID] = None

class DocumentUploadJobResponse(BaseModel):
    id: UUID
    document_id: UUID
    status: ProcessingStatus
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentProcessingJobResponse(BaseModel):
    id: UUID
    document_id: UUID
    status: str
    progress: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    processing_time_ms: int = 0

    class Config:
        from_attributes = True

class DocumentChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    organization_id: Optional[UUID] = None
    workspace_id: Optional[UUID] = None
    chunk_index: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    content: str
    token_count: int = 0
    character_count: int = 0
    checksum: str = ""
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentMetadataResponse(BaseModel):
    id: UUID
    document_id: UUID
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    language: Optional[str] = "en"
    keywords: Optional[dict] = None
    labels: Optional[dict] = None
    categories: Optional[dict] = None
    department: Optional[str] = None
    business_unit: Optional[str] = None
    confidentiality: str
    custom_metadata: Optional[dict] = None
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentMetadataUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    language: Optional[str] = None
    keywords: Optional[dict] = None
    labels: Optional[dict] = None
    categories: Optional[dict] = None
    department: Optional[str] = None
    business_unit: Optional[str] = None
    confidentiality: Optional[str] = None
    custom_metadata: Optional[dict] = None

class DocumentVersionResponse(BaseModel):
    id: UUID
    document_id: UUID
    version_number: int
    storage_path: str
    checksum_sha256: str
    file_size: int
    uploaded_by: Optional[UUID] = None
    change_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentAuditLogResponse(BaseModel):
    id: UUID
    document_id: UUID
    user_id: Optional[UUID] = None
    action: str
    action_metadata: Optional[dict] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class RetentionPolicyResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    retention_days: int
    auto_archive: bool
    auto_delete: bool

    class Config:
        from_attributes = True

class RetentionPolicyUpdate(BaseModel):
    retention_days: int
    auto_archive: bool
    auto_delete: bool
