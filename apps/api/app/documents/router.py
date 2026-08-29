from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, status, Query, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from uuid import UUID
from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db_session
from ..api.dependencies import get_current_user
from ..authorization.organization_resolver import resolve_organization_id
from ..models.user import User
from ..projects.models import Project
from ..workspace.models import Workspace
from .models import Folder, Document
from .dependencies import (
    get_document_service,
    get_metadata_service,
    get_version_service,
    get_lifecycle_service,
    get_governance_service,
    get_history_service
)
from .service import DocumentService
from .preview import DocumentPreviewService
from ..services.metadata_service import MetadataService
from ..services.version_service import VersionService
from ..services.lifecycle_service import LifecycleService
from .governance import GovernanceService
from .history import HistoryService
from .schemas import (
    DocumentResponse,
    DocumentListItem,
    DocumentUpdate,
    DocumentShareRequest,
    DocumentMetadataResponse,
    DocumentMetadataUpdate,
    DocumentVersionResponse,
    DocumentAuditLogResponse,
    RetentionPolicyResponse,
    RetentionPolicyUpdate,
    DocumentProcessingJobResponse,
    DocumentChunkResponse
)
from ..processing.schemas import NormalizedContentModel, ProcessResponse, StatisticsResponse, SectionSchema
from ..processing.pipeline import ProcessingPipeline
from ..processing.models import DocumentContent
from ..storage.factory import StorageProviderFactory

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    workspace_id: Optional[UUID] = Form(None),
    project_id: Optional[UUID] = Form(None),
    folder_id: Optional[UUID] = Form(None),
    title: Optional[str] = Form(None),
    visibility: str = Form("private"),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session),
    service: DocumentService = Depends(get_document_service)
):
    org_uuid = org_id

    # If workspace_id is not supplied, resolve default workspace for org
    if not workspace_id:
        ws_stmt = select(Workspace).where(Workspace.organization_id == org_uuid).order_by(Workspace.created_at.asc())
        ws_res = await db.execute(ws_stmt)
        default_ws = ws_res.scalars().first()
        if default_ws:
            workspace_id = default_ws.id
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found. Please create a workspace in this organization before uploading documents."
            )
    else:
        ws_stmt = select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.organization_id == org_uuid
        )
        ws_res = await db.execute(ws_stmt)
        if not ws_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found."
            )

    if folder_id:
        folder_stmt = select(Folder).where(
            Folder.id == folder_id,
            Folder.organization_id == org_uuid
        )
        folder_res = await db.execute(folder_stmt)
        if not folder_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder does not exist."
            )

    if project_id:
        stmt = select(Project).where(
            Project.id == project_id,
            Project.workspace_id == workspace_id,
            Project.organization_id == org_uuid
        )
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project does not exist."
            )

    file_content = await file.read()
    
    return await service.upload_document(
        file_content=file_content,
        filename=file.filename or "uploaded_document",
        content_type=file.content_type or "application/octet-stream",
        org_id=org_uuid,
        workspace_id=workspace_id,
        project_id=project_id,
        folder_id=folder_id,
        user_id=current_user.id,
        title=title,
        visibility=visibility,
        background_tasks=background_tasks
    )

@router.get("", response_model=List[DocumentListItem])
@router.get("/", response_model=List[DocumentListItem])
async def list_documents(
    workspace_id: Optional[UUID] = Query(None),
    project_id: Optional[UUID] = Query(None),
    folder_id: Optional[UUID] = Query(None),
    query: Optional[str] = Query(None),
    file_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    is_trash: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    org_id: UUID = Depends(resolve_organization_id),
    service: DocumentService = Depends(get_document_service)
):
    return await service.list_documents(
        org_id=org_id,
        workspace_id=workspace_id,
        project_id=project_id,
        folder_id=folder_id,
        search_query=query,
        file_type=file_type,
        status_filter=status_filter,
        is_trash=is_trash,
        limit=limit,
        offset=offset
    )

@router.get("/recent", response_model=List[DocumentListItem])
async def get_recent_documents(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    service: DocumentService = Depends(get_document_service)
):
    return await service.get_recent_documents(org_id=org_id, user_id=current_user.id, limit=limit)

@router.get("/favorites", response_model=List[DocumentListItem])
async def get_favorite_documents(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    service: DocumentService = Depends(get_document_service)
):
    return await service.get_favorite_documents(user_id=current_user.id, org_id=org_id, limit=limit)

@router.patch("/retention", response_model=RetentionPolicyResponse)
async def update_retention_policy(
    policy_in: RetentionPolicyUpdate,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    gov_service = GovernanceService(db)
    return await gov_service.update_retention_policy(
        org_id=org_id,
        retention_days=policy_in.retention_days,
        auto_archive=policy_in.auto_archive,
        auto_delete=policy_in.auto_delete
    )

@router.post("/retention/apply")
async def apply_retention_policy(
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    return {"status": "success", "affected_documents_count": 0}

@router.get("/{id}", response_model=DocumentResponse)
async def get_document(
    id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    service: DocumentService = Depends(get_document_service)
):
    doc = await service.get_document(id, include_deleted=True)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
    return doc

@router.patch("/{id}", response_model=DocumentResponse)
async def update_document(
    id: UUID,
    doc_in: DocumentUpdate,
    org_id: UUID = Depends(resolve_organization_id),
    service: DocumentService = Depends(get_document_service)
):
    doc = await service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
    return await service.update_document(
        doc_id=id,
        title=doc_in.title,
        folder_id=doc_in.folder_id,
        visibility=doc_in.visibility,
        project_id=doc_in.project_id
    )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    id: UUID,
    permanent: bool = Query(False),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    service: DocumentService = Depends(get_document_service)
):
    doc = await service.get_document(id, include_deleted=True)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
    if permanent or doc.deleted_at is not None:
        await service.permanent_delete_document(id)
    else:
        await service.soft_delete_document(id)

@router.post("/{id}/restore", response_model=DocumentResponse)
async def restore_document(
    id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    service: DocumentService = Depends(get_document_service)
):
    return await service.restore_document(id)

@router.get("/{id}/download")
async def download_document(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    service: DocumentService = Depends(get_document_service)
):
    doc = await service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
    
    stream_gen, metadata = await service.get_document_stream(id)
    
    from urllib.parse import quote
    safe_filename = quote(metadata.filename)
    
    return StreamingResponse(
        stream_gen,
        media_type=metadata.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"'
        }
    )

@router.get("/{id}/preview")
async def get_document_preview(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session),
    service: DocumentService = Depends(get_document_service)
):
    doc = await service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
    return await DocumentPreviewService.generate_preview(db, doc)

@router.get("/{id}/intelligence")
async def get_document_intelligence(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session),
    service: DocumentService = Depends(get_document_service)
):
    doc = await service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
    from .models import FileIntelligence
    from ..ai.extraction.file_analyzer import FileIntelligenceAnalyzer

    stmt = select(FileIntelligence).where(FileIntelligence.document_id == id)
    intel = (await db.execute(stmt)).scalar_one_or_none()

    if not intel:
        analyzer = FileIntelligenceAnalyzer(db)
        intel = await analyzer.analyze_document(id)

    return {
        "id": str(intel.id),
        "document_id": str(intel.document_id),
        "organization_id": str(intel.organization_id),
        "workspace_id": str(intel.workspace_id),
        "project_id": str(intel.project_id) if intel.project_id else None,
        "summary": intel.summary,
        "topics": intel.topics or [],
        "keywords": intel.keywords or [],
        "entities": intel.entities or [],
        "facts": intel.facts or [],
        "decisions": intel.decisions or [],
        "tasks": intel.tasks or [],
        "language": intel.language or "en",
        "document_type": intel.document_type or "Unknown",
        "status": intel.status or "COMPLETED",
        "error_message": intel.error_message
    }

@router.post("/{id}/intelligence/reprocess")
async def reprocess_document_intelligence(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session),
    service: DocumentService = Depends(get_document_service)
):
    doc = await service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )

    from ..ai.extraction.file_analyzer import FileIntelligenceAnalyzer
    analyzer = FileIntelligenceAnalyzer(db)
    intel = await analyzer.analyze_document(id)

    return {
        "status": "success",
        "message": "File intelligence successfully reprocessed",
        "intelligence_status": intel.status,
        "document_type": intel.document_type
    }

@router.post("/{id}/favorite")
async def toggle_favorite_document(
    id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    service: DocumentService = Depends(get_document_service)
):
    is_fav = await service.toggle_favorite(current_user.id, id)
    return {"status": "success", "is_favorite": is_fav}

@router.post("/{id}/share")
async def share_document(
    id: UUID,
    share_in: DocumentShareRequest,
    org_id: UUID = Depends(resolve_organization_id),
    service: DocumentService = Depends(get_document_service)
):
    share = await service.share_document(id, share_in.shared_with_user_id, share_in.permission_level)
    return {"status": "success", "shared_with": str(share.shared_with_user_id), "permission_level": share.permission_level}


# --- Metadata Sub-Routes ---

@router.get("/{id}/metadata", response_model=DocumentMetadataResponse)
async def get_document_metadata(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    service: DocumentService = Depends(get_document_service),
    meta_service: MetadataService = Depends(get_metadata_service)
):
    doc = await service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
    return await meta_service.get_metadata(id)

@router.patch("/{id}/metadata", response_model=DocumentMetadataResponse)
async def update_document_metadata(
    id: UUID,
    metadata_in: DocumentMetadataUpdate,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    service: DocumentService = Depends(get_document_service),
    meta_service: MetadataService = Depends(get_metadata_service)
):
    doc = await service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
    return await meta_service.update_metadata(
        document_id=id,
        user_id=current_user.id,
        update_data=metadata_in.dict(exclude_unset=True)
    )

# --- Versioning Sub-Routes ---

@router.get("/{id}/versions", response_model=List[DocumentVersionResponse])
async def list_document_versions(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    service: DocumentService = Depends(get_document_service),
    v_service: VersionService = Depends(get_version_service)
):
    doc = await service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
    return await v_service.list_versions(id)

@router.post("/{id}/versions", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document_version(
    id: UUID,
    file: UploadFile = File(...),
    change_summary: str = Form("Manual Version Upload"),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    service: DocumentService = Depends(get_document_service),
    v_service: VersionService = Depends(get_version_service)
):
    doc = await service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
    file_content = await file.read()
    return await v_service.create_version(
        document_id=id,
        file_content=file_content,
        filename=file.filename,
        content_type=file.content_type,
        user_id=current_user.id,
        change_summary=change_summary
    )

@router.post("/{id}/versions/{version}/restore", response_model=DocumentResponse)
async def restore_document_version(
    id: UUID,
    version: int,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    service: DocumentService = Depends(get_document_service),
    v_service: VersionService = Depends(get_version_service)
):
    doc = await service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
    return await v_service.restore_version(
        document_id=id,
        version_number=version,
        user_id=current_user.id
    )

@router.get("/{id}/versions/{version}")
async def download_document_version(
    id: UUID,
    version: int,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session),
    service: DocumentService = Depends(get_document_service)
):
    doc = await service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
    
    # Resolve the storage path for the selected version
    stmt = select(DocumentVersion).where(
        DocumentVersion.document_id == id,
        DocumentVersion.version_number == version
    )
    result = await db.execute(stmt)
    ver = result.scalar_one_or_none()
    if not ver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} was not found."
        )
        
    provider = StorageProviderFactory.get_provider()
    stream_gen = provider.stream(ver.storage_path)
    
    from urllib.parse import quote
    safe_filename = quote(doc.filename)
    
    return StreamingResponse(
        stream_gen,
        media_type=doc.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"'
        }
    )

# --- Lifecycle Sub-Routes ---

@router.post("/{id}/archive", response_model=DocumentResponse)
async def archive_document(
    id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    service: DocumentService = Depends(get_document_service),
    lc_service: LifecycleService = Depends(get_lifecycle_service)
):
    doc = await service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
    return await lc_service.archive(id, current_user.id)

@router.post("/{id}/restore", response_model=DocumentResponse)
async def restore_document(
    id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    service: DocumentService = Depends(get_document_service),
    lc_service: LifecycleService = Depends(get_lifecycle_service)
):
    # This endpoint bypasses active checks so soft-deleted documents can be retrieved and restored
    return await lc_service.restore(id, current_user.id)

# --- History Sub-Routes ---

@router.get("/{id}/history", response_model=List[DocumentAuditLogResponse])
async def get_document_history(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    service: DocumentService = Depends(get_document_service),
    hist_service: HistoryService = Depends(get_history_service)
):
    doc = await service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
    return await hist_service.get_audit_history(id)

# --- Content Intelligence Sub-Routes ---

@router.post("/{id}/process", response_model=ProcessResponse)
async def process_document_pipeline(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session),
    service: DocumentService = Depends(get_document_service)
):
    doc = await service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
    
    pipeline = ProcessingPipeline(db)
    await pipeline.process_document(id)
    await db.commit()
    
    return ProcessResponse(
        document_id=id,
        status="success",
        message="Document processing pipeline executed successfully."
    )

@router.get("/{id}/content", response_model=NormalizedContentModel)
async def get_document_content(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session),
    service: DocumentService = Depends(get_document_service)
):
    doc = await service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
    
    stmt = select(DocumentContent).where(DocumentContent.document_id == id)
    result = await db.execute(stmt)
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document content has not been extracted yet. Please trigger processing."
        )
        
    return content.content_json

@router.get("/{id}/structure", response_model=List[SectionSchema])
async def get_document_structure(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session),
    service: DocumentService = Depends(get_document_service)
):
    doc = await service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
    
    stmt = select(DocumentContent).where(DocumentContent.document_id == id)
    result = await db.execute(stmt)
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document content has not been extracted yet."
        )
        
    return content.content_json.get("sections", [])

@router.get("/{id}/statistics", response_model=StatisticsResponse)
async def get_document_statistics(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session),
    service: DocumentService = Depends(get_document_service)
):
    doc = await service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
    
    stmt = select(DocumentContent).where(DocumentContent.document_id == id)
    result = await db.execute(stmt)
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document content has not been extracted yet."
        )
        
    stats = content.statistics
    return StatisticsResponse(
        document_id=id,
        word_count=stats.get("word_count", 0),
        character_count=stats.get("character_count", 0),
        page_count=stats.get("page_count", 1),
        table_count=stats.get("table_count", 0),
        image_count=stats.get("image_count", 0)
    )

# ==============================================================================
# PHASE 3.2 PROCESSING STATUS & CHUNKS ENDPOINTS
# ==============================================================================

@router.get("/{id}/processing", response_model=DocumentProcessingJobResponse, tags=["Document Ingestion & Chunking"])
async def get_document_processing_status(
    id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Fetches real-time processing status, progress percentage, and errors for a document."""
    from .models import DocumentProcessingJob

    stmt = select(DocumentProcessingJob).where(
        DocumentProcessingJob.document_id == id,
        DocumentProcessingJob.deleted_at.is_(None)
    ).order_by(DocumentProcessingJob.created_at.desc())

    res = await db.execute(stmt)
    job = res.scalars().first()

    if not job:
        # Check if document exists
        doc_stmt = select(Document).where(Document.id == id, Document.organization_id == org_id)
        doc = (await db.execute(doc_stmt)).scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        # Return default status based on Document record
        return DocumentProcessingJobResponse(
            id=id,
            document_id=id,
            status=doc.processing_status or "QUEUED",
            progress=100.0 if doc.processing_status == "COMPLETED" else 0.0,
            started_at=doc.created_at,
            completed_at=doc.updated_at if doc.processing_status == "COMPLETED" else None,
            error_message=None,
            retry_count=0,
            processing_time_ms=0
        )

    return DocumentProcessingJobResponse(
        id=job.id,
        document_id=job.document_id,
        status=job.status,
        progress=job.progress,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        retry_count=job.retry_count,
        processing_time_ms=job.processing_time_ms
    )

@router.get("/{id}/chunks", response_model=List[DocumentChunkResponse], tags=["Document Ingestion & Chunking"])
async def list_document_chunks(
    id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Lists extracted intelligent chunks for a document ordered by chunk_index."""
    from ..ai.embeddings.models import DocumentChunk

    # Verify doc permission
    doc_stmt = select(Document).where(Document.id == id, Document.organization_id == org_id)
    doc = (await db.execute(doc_stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    chunk_stmt = select(DocumentChunk).where(
        DocumentChunk.document_id == id
    ).order_by(DocumentChunk.chunk_index.asc())

    res = await db.execute(chunk_stmt)
    chunks = res.scalars().all()

    return [
        DocumentChunkResponse(
            id=c.id,
            document_id=c.document_id,
            organization_id=c.organization_id,
            workspace_id=c.workspace_id,
            chunk_index=c.chunk_index,
            page_number=c.page_number,
            section_title=c.section_title,
            content=c.content,
            token_count=c.token_count,
            character_count=c.character_count,
            checksum=c.checksum,
            metadata_json=c.metadata_json,
            created_at=c.created_at
        ) for c in chunks
    ]

@router.post("/{id}/reprocess", response_model=DocumentProcessingJobResponse, tags=["Document Ingestion & Chunking"])
async def reprocess_document_endpoint(
    id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Triggers background text extraction and semantic chunking reprocessing job."""
    from .models import DocumentProcessingJob
    from ..processing.jobs import process_document_job

    doc_stmt = select(Document).where(Document.id == id, Document.organization_id == org_id)
    doc = (await db.execute(doc_stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    doc.processing_status = "QUEUED"

    job = DocumentProcessingJob(
        document_id=id,
        status="QUEUED",
        progress=0.0,
        started_at=None,
        completed_at=None,
        error_message=None,
        retry_count=0,
        processing_time_ms=0
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Trigger background pipeline processing
    background_tasks.add_task(process_document_job, id)

    return DocumentProcessingJobResponse(
        id=job.id,
        document_id=job.document_id,
        status=job.status,
        progress=job.progress,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        retry_count=job.retry_count,
        processing_time_ms=job.processing_time_ms
    )

@router.post("/{id}/reindex", tags=["Document Ingestion & Chunking"])
async def reindex_document_endpoint(
    id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Idempotently re-indexes a document by deleting existing chunks and re-running ingestion and embedding."""
    from .models import Document
    from ..ai.embeddings.models import DocumentChunk, DocumentEmbedding
    from sqlalchemy import delete

    doc_stmt = select(Document).where(Document.id == id, Document.organization_id == org_id)
    doc = (await db.execute(doc_stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    # 1. Clean up old embeddings and chunks to prevent duplicates
    await db.execute(delete(DocumentEmbedding).where(DocumentEmbedding.document_id == id))
    await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == id))

    doc.processing_status = "EXTRACTING"
    await db.commit()

    # 2. Trigger background re-indexing
    from ..processing.jobs import process_document_job
    background_tasks.add_task(process_document_job, id)

    return {"message": "Document re-indexing initiated successfully", "document_id": str(id), "status": "EXTRACTING"}
