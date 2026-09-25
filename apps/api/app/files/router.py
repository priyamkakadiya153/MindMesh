import hashlib
import io
import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc, asc, func
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta, time

from ..database.session import get_session
from ..api.dependencies import get_current_user, get_current_user_from_header_or_query
from ..models.user import User
from ..models.organization_member import OrganizationMember
from ..models.conversations import Conversation, ConversationMember, DirectMessage
from ..models.attachments import Attachment, AttachmentVersion, AttachmentAccessLog, AttachmentShare
from ..workspace.models import WorkspaceMember
from ..storage.local_provider import default_storage_provider
from ..websocket.manager import manager
from ..activity.service import ActivityService
from ..dashboard.service import DashboardService

logger = logging.getLogger("mindmesh.files")
router = APIRouter()

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024 # 50 MB

class FileResponse(BaseModel):
    id: UUID
    organization_id: UUID
    workspace_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    message_id: Optional[UUID] = None
    folder_id: Optional[UUID] = None
    uploaded_by: UUID
    uploader_name: Optional[str] = None
    original_filename: str
    storage_filename: str
    mime_type: str
    file_size: int
    checksum: Optional[str] = None
    storage_path: str
    thumbnail_path: Optional[str] = None
    preview_url: str
    download_url: str
    version: int = 1
    status: str = "active"
    processing_status: str = "ready"
    scan_status: str = "Safe" # Uploading, Scanning, Safe, Rejected, Indexed
    download_count: int = 0
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    source_type: str = "direct" # "conversation", "project", "direct", "workspace", "share"
    source_title: Optional[str] = None
    shared_with: Optional[List[str]] = None
    is_promoted_to_document: bool = False
    promoted_document_id: Optional[UUID] = None

class PaginatedFileResponse(BaseModel):
    items: List[FileResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class FileUpdatePayload(BaseModel):
    original_filename: Optional[str] = Field(None, min_length=1, max_length=255)
    folder_id: Optional[UUID] = None

class PromoteFilePayload(BaseModel):
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    title: Optional[str] = None

class ShareFilePayload(BaseModel):
    recipient_user_ids: Optional[List[UUID]] = None
    recipient_emails: Optional[List[str]] = None
    permission: str = "view" # view, edit, admin
    workspace_id: Optional[UUID] = None

class FileShareRecipientResponse(BaseModel):
    id: UUID
    attachment_id: UUID
    shared_by: UUID
    sharer_name: Optional[str] = None
    sharer_email: Optional[str] = None
    shared_with: UUID
    user_id: UUID
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    avatar_url: Optional[str] = None
    permission: str
    status: str
    shared_at: datetime

class ShareFileResponse(BaseModel):
    status: str = "success"
    message: str
    shared_count: int
    shares: List[FileShareRecipientResponse]

class AttachmentVersionResponse(BaseModel):
    id: UUID
    attachment_id: UUID
    version_number: int
    storage_filename: str
    file_size: int
    checksum: Optional[str] = None
    created_by: UUID
    creator_name: Optional[str] = None
    created_at: datetime

class AttachmentAccessLogResponse(BaseModel):
    id: UUID
    attachment_id: UUID
    user_id: UUID
    user_name: Optional[str] = None
    action: str
    ip_address: Optional[str] = None
    accessed_at: datetime

class StorageStatsResponse(BaseModel):
    total_bytes: int
    total_files: int
    by_category: Dict[str, int]
    largest_files: List[FileResponse]

async def verify_conversation_access(db: AsyncSession, conversation_id: UUID, user_id: UUID) -> Conversation:
    conv_stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.is_active == True,
        Conversation.deleted_at == None
    )
    res = await db.execute(conv_stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    if conv.visibility != "public":
        mem_stmt = select(ConversationMember).where(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id == user_id
        )
        m_res = await db.execute(mem_stmt)
        if not m_res.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to conversation files.")

    return conv

async def verify_file_access(db: AsyncSession, attachment: Attachment, user_id: UUID):
    # 1. Direct uploader always has access
    if attachment.uploaded_by == user_id:
        return

    # 2. Check if explicitly shared with the user
    share_stmt = select(AttachmentShare).where(
        AttachmentShare.attachment_id == attachment.id,
        AttachmentShare.shared_with == user_id,
        AttachmentShare.status == "active"
    )
    share_res = await db.execute(share_stmt)
    if share_res.scalar_one_or_none():
        return

    # 3. Check conversation membership if conversation attachment
    if attachment.conversation_id:
        await verify_conversation_access(db, attachment.conversation_id, user_id)
        return

    # 4. Check workspace member access if workspace file
    if attachment.workspace_id:
        wm_stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == attachment.workspace_id,
            WorkspaceMember.user_id == user_id
        )
        wm_res = await db.execute(wm_stmt)
        if wm_res.scalar_one_or_none():
            return

    # 5. Check organization membership
    stmt = select(OrganizationMember).where(
        OrganizationMember.organization_id == attachment.organization_id,
        OrganizationMember.user_id == user_id,
        OrganizationMember.is_active == True
    )
    res = await db.execute(stmt)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to organization files.")

async def log_audit_event(db: AsyncSession, attachment_id: UUID, user_id: UUID, action: str, request: Optional[Request] = None):
    try:
        ip = request.client.host if request and request.client else None
        log = AttachmentAccessLog(
            id=uuid4(),
            attachment_id=attachment_id,
            user_id=user_id,
            action=action,
            ip_address=ip,
            accessed_at=datetime.utcnow()
        )
        db.add(log)
    except Exception as e:
        logger.warning(f"Failed to record audit log: {e}")

async def simulate_background_indexing(file_id: UUID, org_id: UUID, user_id: UUID):
    """Placeholder background job architecture for AI indexing & virus scanning."""
    import asyncio
    await asyncio.sleep(0.5)

@router.get("/storage/stats", response_model=StorageStatsResponse)
async def get_storage_stats(
    organization_id: Optional[UUID] = Query(None),
    workspace_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    resolved_org_id = organization_id
    if not resolved_org_id:
        mem_stmt = select(OrganizationMember.organization_id).where(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.is_active == True
        ).limit(1)
        res = await db.execute(mem_stmt)
        resolved_org_id = res.scalar_one_or_none()

    if not resolved_org_id:
        return StorageStatsResponse(total_bytes=0, total_files=0, by_category={}, largest_files=[])

    base_query = select(Attachment).where(
        Attachment.organization_id == resolved_org_id,
        Attachment.status == "active",
        Attachment.is_active == True
    )
    if workspace_id:
        base_query = base_query.where(or_(Attachment.workspace_id == workspace_id, Attachment.workspace_id == None))

    res = await db.execute(base_query)
    all_atts = res.scalars().all()

    total_bytes = sum(a.file_size for a in all_atts)
    total_files = len(all_atts)

    categories = {"images": 0, "documents": 0, "code": 0, "media": 0, "archives": 0, "other": 0}
    for a in all_atts:
        m = a.mime_type.lower()
        if m.startswith("image/"):
            categories["images"] += a.file_size
        elif "pdf" in m or "word" in m or "document" in m or "spreadsheet" in m or "text/plain" in m or "csv" in m:
            categories["documents"] += a.file_size
        elif "json" in m or "javascript" in m or "python" in m or "typescript" in m or "html" in m or "css" in m or "xml" in m:
            categories["code"] += a.file_size
        elif m.startswith("video/") or m.startswith("audio/"):
            categories["media"] += a.file_size
        elif "zip" in m or "tar" in m or "rar" in m or "7z" in m or "gzip" in m:
            categories["archives"] += a.file_size
        else:
            categories["other"] += a.file_size

    # Top 5 largest files
    largest_stmt = select(Attachment, User).join(User, Attachment.uploaded_by == User.id).where(
        Attachment.organization_id == resolved_org_id,
        Attachment.status == "active",
        Attachment.is_active == True
    ).order_by(desc(Attachment.file_size)).limit(5)
    l_res = await db.execute(largest_stmt)
    largest_files = []
    for att, uploader in l_res.all():
        largest_files.append(FileResponse(
            id=att.id,
            organization_id=att.organization_id,
            workspace_id=att.workspace_id,
            folder_id=att.folder_id,
            conversation_id=att.conversation_id,
            message_id=att.message_id,
            uploaded_by=att.uploaded_by,
            uploader_name=uploader.full_name,
            original_filename=att.original_filename,
            storage_filename=att.storage_filename,
            mime_type=att.mime_type,
            file_size=att.file_size,
            checksum=att.checksum,
            storage_path=att.storage_path,
            preview_url=f"/api/v1/files/{att.id}/preview",
            download_url=f"/api/v1/files/{att.id}/download",
            version=att.version,
            status=att.status,
            processing_status=att.processing_status or "ready",
            scan_status="Safe",
            download_count=att.download_count,
            created_at=att.created_at,
            updated_at=att.updated_at,
            deleted_at=att.deleted_at
        ))

    return StorageStatsResponse(
        total_bytes=total_bytes,
        total_files=total_files,
        by_category=categories,
        largest_files=largest_files
    )

@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    organization_id: Optional[UUID] = Form(None),
    workspace_id: Optional[UUID] = Form(None),
    folder_id: Optional[UUID] = Form(None),
    conversation_id: Optional[UUID] = Form(None),
    message_id: Optional[UUID] = Form(None),
    force_duplicate: bool = Form(False),
    shared_with_user_ids: Optional[str] = Form(None), # comma-separated or JSON list of UUIDs
    recipient_emails: Optional[str] = Form(None), # comma-separated or JSON list of emails
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    try:
        resolved_org_id = organization_id
        if conversation_id:
            conv = await verify_conversation_access(db, conversation_id, current_user.id)
            resolved_org_id = conv.organization_id
            if not workspace_id:
                workspace_id = conv.workspace_id
        
        if not resolved_org_id:
            mem_stmt = select(OrganizationMember.organization_id).where(
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.is_active == True
            ).limit(1)
            res = await db.execute(mem_stmt)
            resolved_org_id = res.scalar_one_or_none()
            if not resolved_org_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active organization found for user.")

        file_bytes = await file.read()
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File exceeds 50 MB.")

        if len(file_bytes) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

        checksum = hashlib.sha256(file_bytes).hexdigest()

        # Duplicate Detection
        if not force_duplicate:
            dup_stmt = select(Attachment, User).join(User, Attachment.uploaded_by == User.id).where(
                Attachment.organization_id == resolved_org_id,
                Attachment.checksum == checksum,
                Attachment.status == "active",
                Attachment.is_active == True
            )
            dup_res = await db.execute(dup_stmt)
            existing_dup = dup_res.first()
            if existing_dup:
                att_dup, uploader_dup = existing_dup
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "DuplicateFile",
                        "message": f"Identical file already exists: '{att_dup.original_filename}'.",
                        "existing_file_id": str(att_dup.id),
                        "existing_filename": att_dup.original_filename,
                        "uploaded_by": uploader_dup.full_name,
                        "created_at": att_dup.created_at.isoformat()
                    }
                )

        original_filename = file.filename or "attachment"
        mime_type = file.content_type or "application/octet-stream"

        # Executable and dangerous file validation
        import os
        ext = os.path.splitext(original_filename)[1].lower()
        unsafe_extensions = {".exe", ".bat", ".cmd", ".sh", ".ps1", ".dll", ".scr", ".vbs", ".js", ".jar", ".com", ".msi", ".bin"}
        if ext in unsafe_extensions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File extension '{ext}' is not permitted for security reasons.")

        try:
            storage_filename, relative_path = await default_storage_provider.save_file(file_bytes, original_filename)
        except Exception as st_err:
            logger.exception(f"Storage save error: {st_err}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Storage unavailable.")

        att_id = uuid4()
        now = datetime.utcnow()

        attachment = Attachment(
            id=att_id,
            organization_id=resolved_org_id,
            workspace_id=workspace_id,
            folder_id=folder_id,
            conversation_id=conversation_id,
            message_id=message_id,
            uploaded_by=current_user.id,
            original_filename=original_filename,
            storage_filename=storage_filename,
            mime_type=mime_type,
            file_size=len(file_bytes),
            checksum=checksum,
            storage_path=relative_path,
            version=1,
            status="active",
            processing_status="ready",
            download_count=0,
            created_at=now,
            updated_at=now
        )
        db.add(attachment)

        version_entry = AttachmentVersion(
            id=uuid4(),
            attachment_id=att_id,
            version_number=1,
            storage_filename=storage_filename,
            file_size=len(file_bytes),
            checksum=checksum,
            storage_path=relative_path,
            created_by=current_user.id,
            created_at=now,
            updated_at=now
        )
        db.add(version_entry)

        # Parse and persist initial recipient shares if provided
        target_recipients = set()
        if shared_with_user_ids:
            try:
                import json
                if shared_with_user_ids.startswith("["):
                    parsed_uids = json.loads(shared_with_user_ids)
                    for uid in parsed_uids:
                        target_recipients.add(UUID(str(uid)))
                else:
                    for uid_str in shared_with_user_ids.split(","):
                        if uid_str.strip():
                            target_recipients.add(UUID(uid_str.strip()))
            except Exception as e:
                logger.warning(f"Failed to parse shared_with_user_ids: {e}")

        if recipient_emails:
            try:
                import json
                clean_emails = []
                if recipient_emails.startswith("["):
                    clean_emails = [e.strip().lower() for e in json.loads(recipient_emails) if isinstance(e, str) and e.strip()]
                else:
                    clean_emails = [e.strip().lower() for e in recipient_emails.split(",") if e.strip()]
                if clean_emails:
                    u_stmt = select(User.id).where(func.lower(User.email).in_(clean_emails), User.is_active == True)
                    u_res = await db.execute(u_stmt)
                    for uid in u_res.scalars().all():
                        target_recipients.add(uid)
            except Exception as e:
                logger.warning(f"Failed to parse recipient_emails: {e}")

        target_recipients.discard(current_user.id)
        if target_recipients:
            org_mems_stmt = select(OrganizationMember.user_id).where(
                OrganizationMember.organization_id == resolved_org_id,
                OrganizationMember.user_id.in_(target_recipients),
                OrganizationMember.is_active == True
            )
            org_mems_res = await db.execute(org_mems_stmt)
            for r_uid in org_mems_res.scalars().all():
                share_row = AttachmentShare(
                    id=uuid4(),
                    attachment_id=att_id,
                    organization_id=resolved_org_id,
                    workspace_id=workspace_id,
                    shared_by=current_user.id,
                    shared_with=r_uid,
                    permission="view",
                    source_type="direct",
                    status="active",
                    shared_at=now
                )
                db.add(share_row)

        await log_audit_event(db, att_id, current_user.id, "upload", request)

        try:
            act_service = ActivityService(db)
            await act_service.record_event(
                org_id=resolved_org_id,
                user_id=current_user.id,
                event_type="file_uploaded",
                workspace_id=workspace_id,
                metadata={
                    "file_id": str(att_id),
                    "filename": original_filename,
                    "size": len(file_bytes),
                    "mime_type": mime_type
                }
            )
        except Exception:
            pass

        await db.commit()

        background_tasks.add_task(simulate_background_indexing, att_id, resolved_org_id, current_user.id)

        try:
            dash_service = DashboardService(db)
            await dash_service.refresh_dashboard(current_user.id, resolved_org_id)
        except Exception:
            pass

        if conversation_id:
            try:
                m_stmt = select(ConversationMember.user_id).where(ConversationMember.conversation_id == conversation_id)
                m_res = await db.execute(m_stmt)
                member_user_ids = [str(u) for u in m_res.scalars().all()]
                await manager.broadcast_to_users({
                    "event": "file_uploaded",
                    "file": {
                        "id": str(attachment.id),
                        "conversation_id": str(conversation_id),
                        "original_filename": attachment.original_filename,
                        "mime_type": attachment.mime_type,
                        "file_size": attachment.file_size,
                        "uploader_name": current_user.full_name
                    }
                }, member_user_ids)
            except Exception:
                pass

        file_resps = await build_file_responses(db, [(attachment, current_user)], current_user.id)
        return file_resps[0]

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"[FILE UPLOAD EXCEPTION] User={current_user.id}: {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Upload failed. Please try again.")

async def build_file_responses(
    db: AsyncSession,
    attachments_with_uploaders: List[tuple[Attachment, User]],
    current_user_id: UUID
) -> List[FileResponse]:
    if not attachments_with_uploaders:
        return []

    # 1. Collect conversation_ids and checksums to batch fetch metadata
    att_ids = [att.id for att, _ in attachments_with_uploaders]
    conv_ids = [att.conversation_id for att, _ in attachments_with_uploaders if att.conversation_id]
    checksums = [att.checksum for att, _ in attachments_with_uploaders if att.checksum]
    filenames = [att.original_filename for att, _ in attachments_with_uploaders]
    org_ids = list({att.organization_id for att, _ in attachments_with_uploaders})

    # Fetch active shares for all attachments
    shares_map: Dict[UUID, List[str]] = {}
    shares_recipient_ids: Dict[UUID, List[UUID]] = {}
    if att_ids:
        s_stmt = select(AttachmentShare.attachment_id, User).join(
            User, AttachmentShare.shared_with == User.id
        ).where(
            AttachmentShare.attachment_id.in_(att_ids),
            AttachmentShare.status == "active"
        )
        s_res = await db.execute(s_stmt)
        for aid, u in s_res.all():
            if aid not in shares_map:
                shares_map[aid] = []
                shares_recipient_ids[aid] = []
            uname = u.full_name or u.email
            if uname and uname not in shares_map[aid]:
                shares_map[aid].append(uname)
                shares_recipient_ids[aid].append(u.id)

    conv_map: Dict[UUID, Conversation] = {}
    conv_members_map: Dict[UUID, List[str]] = {}
    if conv_ids:
        c_stmt = select(Conversation).where(Conversation.id.in_(conv_ids))
        c_res = await db.execute(c_stmt)
        for c in c_res.scalars().all():
            conv_map[c.id] = c

        cm_stmt = select(ConversationMember.conversation_id, User).join(
            User, ConversationMember.user_id == User.id
        ).where(ConversationMember.conversation_id.in_(conv_ids))
        cm_res = await db.execute(cm_stmt)
        for cid, u in cm_res.all():
            if cid not in conv_members_map:
                conv_members_map[cid] = []
            name = u.full_name if u else None
            if name and name not in conv_members_map[cid]:
                conv_members_map[cid].append(name)

    # 2. Check promoted Documents in workspace/org
    from ..documents.models import Document
    promoted_doc_map: Dict[str, UUID] = {}
    if org_ids:
        doc_stmt = select(
            Document.id,
            Document.checksum_sha256,
            Document.original_filename,
            Document.organization_id,
            Document.workspace_id
        ).where(
            Document.organization_id.in_(org_ids),
            Document.deleted_at.is_(None)
        )
        if checksums or filenames:
            conds = []
            if checksums:
                conds.append(Document.checksum_sha256.in_(checksums))
            if filenames:
                conds.append(Document.original_filename.in_(filenames))
            doc_stmt = doc_stmt.where(or_(*conds))
        d_res = await db.execute(doc_stmt)
        for doc_id, csum, fname, oid, wid in d_res.all():
            if csum:
                promoted_doc_map[f"{oid}_{csum}"] = doc_id
                if wid:
                    promoted_doc_map[f"{oid}_{wid}_{csum}"] = doc_id
            if fname:
                promoted_doc_map[f"{oid}_{fname}"] = doc_id
                if wid:
                    promoted_doc_map[f"{oid}_{wid}_{fname}"] = doc_id

    items = []
    for att, uploader in attachments_with_uploaders:
        source_type = "direct"
        source_title = "Direct Shared File"
        shared_with = shares_map.get(att.id, [])
        recipients = shares_recipient_ids.get(att.id, [])

        if att.conversation_id and att.conversation_id in conv_map:
            conv = conv_map[att.conversation_id]
            source_type = "conversation"
            source_title = conv.name or ("Direct Message" if conv.type == "direct" else "Team Chat")
            all_members = conv_members_map.get(att.conversation_id, [])
            if not shared_with:
                shared_with = [m for m in all_members if m != uploader.full_name]
        elif shared_with:
            source_type = "share" if current_user_id in recipients else "direct"
            if current_user_id in recipients:
                source_title = f"Shared by {uploader.full_name or uploader.email}"
            else:
                source_title = f"Shared with {', '.join(shared_with)}"
        elif att.workspace_id:
            source_type = "project" if att.folder_id else "workspace"
            source_title = "Workspace / Project File"

        promoted_id = None
        is_promoted = False
        if att.checksum and att.workspace_id and f"{att.organization_id}_{att.workspace_id}_{att.checksum}" in promoted_doc_map:
            promoted_id = promoted_doc_map[f"{att.organization_id}_{att.workspace_id}_{att.checksum}"]
            is_promoted = True
        elif att.checksum and f"{att.organization_id}_{att.checksum}" in promoted_doc_map:
            promoted_id = promoted_doc_map[f"{att.organization_id}_{att.checksum}"]
            is_promoted = True
        elif att.workspace_id and f"{att.organization_id}_{att.workspace_id}_{att.original_filename}" in promoted_doc_map:
            promoted_id = promoted_doc_map[f"{att.organization_id}_{att.workspace_id}_{att.original_filename}"]
            is_promoted = True
        elif f"{att.organization_id}_{att.original_filename}" in promoted_doc_map:
            promoted_id = promoted_doc_map[f"{att.organization_id}_{att.original_filename}"]
            is_promoted = True

        items.append(FileResponse(
            id=att.id,
            organization_id=att.organization_id,
            workspace_id=att.workspace_id,
            folder_id=att.folder_id,
            conversation_id=att.conversation_id,
            message_id=att.message_id,
            uploaded_by=att.uploaded_by,
            uploader_name=uploader.full_name,
            original_filename=att.original_filename,
            storage_filename=att.storage_filename,
            mime_type=att.mime_type,
            file_size=att.file_size,
            checksum=att.checksum,
            storage_path=att.storage_path,
            preview_url=f"/api/v1/files/{att.id}/preview",
            download_url=f"/api/v1/files/{att.id}/download",
            version=att.version,
            status=att.status,
            processing_status=att.processing_status or "ready",
            scan_status="Safe",
            download_count=att.download_count,
            created_at=att.created_at,
            updated_at=att.updated_at,
            deleted_at=att.deleted_at,
            source_type=source_type,
            source_title=source_title,
            shared_with=shared_with,
            is_promoted_to_document=is_promoted,
            promoted_document_id=promoted_id
        ))
    return items

@router.get("", response_model=PaginatedFileResponse)
async def list_files(
    organization_id: Optional[UUID] = Query(None),
    workspace_id: Optional[UUID] = Query(None),
    folder_id: Optional[UUID] = Query(None),
    conversation_id: Optional[UUID] = Query(None),
    mime_category: Optional[str] = Query(None), # image, document, code, media, archive, pdf, office, text, compressed
    sharing_filter: Optional[str] = Query("all"), # all, shared_with_me, shared_by_me, recent, conversations, projects
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("newest"), # newest, oldest, name_asc, name_desc, size_desc, size_asc, recently_modified
    date_filter: Optional[str] = Query(None), # today, yesterday, last_7_days, this_month
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    if organization_id:
        target_org_ids = [organization_id]
    else:
        mem_stmt = select(OrganizationMember.organization_id).where(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.is_active == True
        )
        res = await db.execute(mem_stmt)
        target_org_ids = [row[0] for row in res.all()]

    if not target_org_ids:
        return PaginatedFileResponse(items=[], total=0, page=page, page_size=page_size, total_pages=0)

    # Resolve user's accessible conversation IDs
    cm_stmt = select(ConversationMember.conversation_id).where(
        ConversationMember.user_id == current_user.id
    )
    cm_res = await db.execute(cm_stmt)
    user_conv_ids = [row[0] for row in cm_res.all()]

    # Subqueries for user's explicit shares
    shared_to_user_subquery = select(AttachmentShare.attachment_id).where(
        AttachmentShare.shared_with == current_user.id,
        AttachmentShare.status == "active"
    )
    shared_by_user_subquery = select(AttachmentShare.attachment_id).where(
        AttachmentShare.shared_by == current_user.id,
        AttachmentShare.status == "active"
    )

    # User's accessible workspaces in this org
    wm_stmt = select(WorkspaceMember.workspace_id).where(
        WorkspaceMember.user_id == current_user.id
    )
    wm_res = await db.execute(wm_stmt)
    user_ws_ids = [row[0] for row in wm_res.all()]

    stmt = select(Attachment, User).join(
        User, Attachment.uploaded_by == User.id
    ).where(
        Attachment.organization_id.in_(target_org_ids),
        Attachment.status == "active",
        Attachment.is_active == True
    )

    # Base Access Condition:
    # 1. User is uploader
    # 2. File was explicitly shared with user
    # 3. File was uploaded in a conversation user is a member of
    # 4. File is in a workspace user is a member of (or general org file without restricted conversation)
    access_condition = or_(
        Attachment.uploaded_by == current_user.id,
        Attachment.id.in_(shared_to_user_subquery),
        Attachment.conversation_id.in_(user_conv_ids) if user_conv_ids else False,
        and_(
            Attachment.conversation_id == None,
            or_(
                Attachment.workspace_id.in_(user_ws_ids) if user_ws_ids else False,
                Attachment.workspace_id == None
            )
        )
    )
    stmt = stmt.where(access_condition)

    # Sharing filters
    if sharing_filter == "shared_with_me":
        # Files explicitly shared with current user OR received in conversations
        stmt = stmt.where(
            Attachment.uploaded_by != current_user.id,
            or_(
                Attachment.id.in_(shared_to_user_subquery),
                Attachment.conversation_id.in_(user_conv_ids) if user_conv_ids else False
            )
        )
    elif sharing_filter == "shared_by_me":
        # Files uploaded by current user OR explicitly shared by current user
        stmt = stmt.where(
            or_(
                Attachment.uploaded_by == current_user.id,
                Attachment.id.in_(shared_by_user_subquery)
            )
        )
    elif sharing_filter == "recent":
        stmt = stmt.where(
            or_(
                Attachment.created_at >= (datetime.utcnow() - timedelta(days=7)),
                Attachment.id.in_(
                    select(AttachmentShare.attachment_id).where(
                        or_(AttachmentShare.shared_with == current_user.id, AttachmentShare.shared_by == current_user.id),
                        AttachmentShare.status == "active",
                        AttachmentShare.shared_at >= (datetime.utcnow() - timedelta(days=7))
                    )
                )
            )
        )
    elif sharing_filter == "conversations":
        stmt = stmt.where(
            Attachment.conversation_id.isnot(None),
            Attachment.conversation_id.in_(user_conv_ids) if user_conv_ids else False
        )
    elif sharing_filter == "projects":
        stmt = stmt.where(
            Attachment.conversation_id == None,
            or_(Attachment.folder_id != None, Attachment.workspace_id != None)
        )

    if workspace_id:
        if sharing_filter in ("conversations", "shared_with_me"):
            # If directly shared with current user or in a DM, do not hide just because workspace_id differs
            pass
        else:
            stmt = stmt.where(or_(
                Attachment.workspace_id == workspace_id,
                Attachment.workspace_id == None,
                Attachment.id.in_(shared_to_user_subquery),
                Attachment.conversation_id.in_(user_conv_ids) if user_conv_ids else False
            ))
    if folder_id:
        stmt = stmt.where(Attachment.folder_id == folder_id)
    if conversation_id:
        stmt = stmt.where(Attachment.conversation_id == conversation_id)
    if search and search.strip():
        term = f"%{search.strip()}%"
        stmt = stmt.where(or_(
            Attachment.original_filename.ilike(term),
            Attachment.mime_type.ilike(term),
            User.full_name.ilike(term)
        ))

    # Category Filters
    if mime_category and mime_category != 'all':
        cat = mime_category.lower()
        if cat == "image" or cat == "images":
            stmt = stmt.where(Attachment.mime_type.startswith("image/"))
        elif cat == "document" or cat == "documents":
            stmt = stmt.where(or_(
                Attachment.mime_type.contains("pdf"),
                Attachment.mime_type.contains("word"),
                Attachment.mime_type.contains("document"),
                Attachment.mime_type.contains("spreadsheet"),
                Attachment.mime_type.contains("text/plain"),
                Attachment.mime_type.contains("csv"),
                Attachment.mime_type.contains("officedocument")
            ))
        elif cat == "pdf":
            stmt = stmt.where(or_(Attachment.mime_type.contains("pdf"), Attachment.original_filename.ilike("%.pdf")))
        elif cat == "office":
            stmt = stmt.where(or_(Attachment.mime_type.contains("word"), Attachment.mime_type.contains("excel"), Attachment.mime_type.contains("powerpoint"), Attachment.mime_type.contains("officedocument")))
        elif cat == "text":
            stmt = stmt.where(or_(Attachment.mime_type.contains("text/plain"), Attachment.mime_type.contains("csv"), Attachment.original_filename.ilike("%.txt"), Attachment.original_filename.ilike("%.md")))
        elif cat == "code":
            stmt = stmt.where(or_(
                Attachment.mime_type.contains("json"),
                Attachment.mime_type.contains("javascript"),
                Attachment.mime_type.contains("typescript"),
                Attachment.mime_type.contains("python"),
                Attachment.mime_type.contains("java"),
                Attachment.mime_type.contains("cpp"),
                Attachment.original_filename.ilike("%.py"),
                Attachment.original_filename.ilike("%.js"),
                Attachment.original_filename.ilike("%.ts"),
                Attachment.original_filename.ilike("%.tsx"),
                Attachment.original_filename.ilike("%.java"),
                Attachment.original_filename.ilike("%.cpp"),
                Attachment.original_filename.ilike("%.json"),
                Attachment.original_filename.ilike("%.md")
            ))
        elif cat == "media":
            stmt = stmt.where(or_(Attachment.mime_type.startswith("video/"), Attachment.mime_type.startswith("audio/")))
        elif cat == "archive" or cat == "archives" or cat == "compressed":
            stmt = stmt.where(or_(
                Attachment.mime_type.contains("zip"),
                Attachment.mime_type.contains("tar"),
                Attachment.mime_type.contains("rar"),
                Attachment.mime_type.contains("7z"),
                Attachment.mime_type.contains("gzip")
            ))

    # Date Filters
    if date_filter:
        now_dt = datetime.utcnow()
        today_start = datetime.combine(now_dt.date(), time.min)
        if date_filter == "today":
            stmt = stmt.where(Attachment.created_at >= today_start)
        elif date_filter == "yesterday":
            yest_start = today_start - timedelta(days=1)
            stmt = stmt.where(and_(Attachment.created_at >= yest_start, Attachment.created_at < today_start))
        elif date_filter == "last_7_days":
            stmt = stmt.where(Attachment.created_at >= today_start - timedelta(days=7))
        elif date_filter == "this_month":
            month_start = datetime(now_dt.year, now_dt.month, 1)
            stmt = stmt.where(Attachment.created_at >= month_start)

    # Count Query
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Sorting
    if sort_by == "oldest":
        stmt = stmt.order_by(asc(Attachment.created_at))
    elif sort_by == "name_asc":
        stmt = stmt.order_by(asc(Attachment.original_filename))
    elif sort_by == "name_desc":
        stmt = stmt.order_by(desc(Attachment.original_filename))
    elif sort_by == "size_desc":
        stmt = stmt.order_by(desc(Attachment.file_size))
    elif sort_by == "size_asc":
        stmt = stmt.order_by(asc(Attachment.file_size))
    elif sort_by == "recently_modified":
        stmt = stmt.order_by(desc(Attachment.updated_at))
    else: # newest default
        stmt = stmt.order_by(desc(Attachment.created_at))

    # Pagination
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    res = await db.execute(stmt)
    rows = res.all()

    items = await build_file_responses(db, [(att, uploader) for att, uploader in rows], current_user.id)
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return PaginatedFileResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{id}", response_model=FileResponse)
async def get_file_details(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Attachment, User).join(
        User, Attachment.uploaded_by == User.id
    ).where(Attachment.id == id)
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")

    att, uploader = row
    await verify_file_access(db, att, current_user.id)

    file_resps = await build_file_responses(db, [(att, uploader)], current_user.id)
    return file_resps[0]

@router.post("/{id}/share", response_model=ShareFileResponse)
async def share_file(
    id: UUID,
    payload: ShareFilePayload,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Attachment, User).join(User, Attachment.uploaded_by == User.id).where(
        Attachment.id == id,
        Attachment.status == "active",
        Attachment.deleted_at == None
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")

    attachment, uploader = row
    await verify_file_access(db, attachment, current_user.id)

    target_user_ids = set(payload.recipient_user_ids or [])

    if payload.recipient_emails:
        clean_emails = [e.strip().lower() for e in payload.recipient_emails if e.strip()]
        if clean_emails:
            u_stmt = select(User.id).where(func.lower(User.email).in_(clean_emails), User.is_active == True)
            u_res = await db.execute(u_stmt)
            for uid in u_res.scalars().all():
                target_user_ids.add(uid)

    # Disallow sharing with oneself
    target_user_ids.discard(current_user.id)

    if not target_user_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid recipient users provided.")

    # Validate that recipients exist and are active in organization
    org_mems_stmt = select(OrganizationMember.user_id).where(
        OrganizationMember.organization_id == attachment.organization_id,
        OrganizationMember.user_id.in_(target_user_ids),
        OrganizationMember.is_active == True
    )
    org_mems_res = await db.execute(org_mems_stmt)
    valid_org_user_ids = set(org_mems_res.scalars().all())

    # Fallback: if not found under attachment.organization_id directly, check any active organization current_user belongs to
    if not valid_org_user_ids:
        shared_orgs_stmt = select(OrganizationMember.user_id).where(
            OrganizationMember.organization_id.in_(
                select(OrganizationMember.organization_id).where(
                    OrganizationMember.user_id == current_user.id,
                    OrganizationMember.is_active == True
                )
            ),
            OrganizationMember.user_id.in_(target_user_ids),
            OrganizationMember.is_active == True
        )
        so_res = await db.execute(shared_orgs_stmt)
        valid_org_user_ids = set(so_res.scalars().all())

    if not valid_org_user_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recipients must be members of the organization.")

    now = datetime.utcnow()
    # Check existing shares
    existing_shares_stmt = select(AttachmentShare).where(
        AttachmentShare.attachment_id == id,
        AttachmentShare.shared_with.in_(valid_org_user_ids)
    )
    es_res = await db.execute(existing_shares_stmt)
    existing_shares_map = {s.shared_with: s for s in es_res.scalars().all()}

    saved_shares = []
    notified_recipients = []
    for uid in valid_org_user_ids:
        if uid in existing_shares_map:
            s = existing_shares_map[uid]
            s.status = "active"
            s.shared_by = current_user.id
            s.permission = payload.permission or "view"
            s.shared_at = now
            saved_shares.append(s)
        else:
            s = AttachmentShare(
                id=uuid4(),
                attachment_id=id,
                organization_id=attachment.organization_id,
                workspace_id=payload.workspace_id or attachment.workspace_id,
                shared_by=current_user.id,
                shared_with=uid,
                permission=payload.permission or "view",
                source_type="direct",
                status="active",
                shared_at=now
            )
            db.add(s)
            saved_shares.append(s)
        notified_recipients.append(str(uid))

    await log_audit_event(db, id, current_user.id, "share", request)
    await db.commit()

    # Query recipient users
    recip_stmt = select(User).where(User.id.in_(valid_org_user_ids))
    recip_res = await db.execute(recip_stmt)
    recip_map = {u.id: u for u in recip_res.scalars().all()}

    shares_resp_list: List[FileShareRecipientResponse] = []
    for s in saved_shares:
        recip_user = recip_map.get(s.shared_with)
        r_name = (recip_user.full_name or recip_user.email) if recip_user else "Member"
        r_email = recip_user.email if recip_user else ""
        shares_resp_list.append(FileShareRecipientResponse(
            id=s.id,
            attachment_id=s.attachment_id,
            shared_by=s.shared_by,
            sharer_name=current_user.full_name or current_user.email,
            sharer_email=current_user.email,
            shared_with=s.shared_with,
            user_id=s.shared_with,
            recipient_name=r_name,
            recipient_email=r_email,
            avatar_url=getattr(recip_user, 'avatar_url', None) if recip_user else None,
            permission=s.permission,
            status=s.status,
            shared_at=s.shared_at
        ))

    # Real-time WebSocket event
    if notified_recipients:
        try:
            await manager.broadcast_to_users({
                "event": "file_shared",
                "file": {
                    "id": str(attachment.id),
                    "original_filename": attachment.original_filename,
                    "mime_type": attachment.mime_type,
                    "file_size": attachment.file_size,
                    "shared_by": current_user.full_name or current_user.email,
                    "shared_at": now.isoformat()
                }
            }, notified_recipients)
        except Exception:
            pass

    recipient_names = [r.recipient_name for r in shares_resp_list if r.recipient_name]
    names_str = ", ".join(recipient_names)
    count = len(shares_resp_list)
    msg = f"File successfully shared with {count} member(s): {names_str}." if count > 0 else "File successfully shared."

    return ShareFileResponse(
        status="success",
        message=msg,
        shared_count=count,
        shares=shares_resp_list
    )

@router.get("/{id}/shares", response_model=List[FileShareRecipientResponse])
async def list_file_shares(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Attachment).where(Attachment.id == id)
    res = await db.execute(stmt)
    att = res.scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")

    await verify_file_access(db, att, current_user.id)

    s_stmt = select(AttachmentShare, User).join(User, AttachmentShare.shared_with == User.id).where(
        AttachmentShare.attachment_id == id,
        AttachmentShare.status == "active"
    ).order_by(desc(AttachmentShare.shared_at))
    s_res = await db.execute(s_stmt)
    shares = []
    for share, recipient in s_res.all():
        shares.append(FileShareRecipientResponse(
            id=share.id,
            attachment_id=share.attachment_id,
            shared_by=share.shared_by,
            sharer_name=None,
            sharer_email=None,
            shared_with=recipient.id,
            user_id=recipient.id,
            recipient_name=recipient.full_name or recipient.email,
            recipient_email=recipient.email,
            avatar_url=getattr(recipient, 'avatar_url', None),
            permission=share.permission,
            status=share.status,
            shared_at=share.shared_at
        ))
    return shares

@router.delete("/{id}/share")
async def revoke_file_share(
    id: UUID,
    recipient_user_id: Optional[UUID] = Query(None),
    share_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Attachment).where(Attachment.id == id)
    res = await db.execute(stmt)
    att = res.scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")

    await verify_file_access(db, att, current_user.id)

    s_stmt = select(AttachmentShare).where(
        AttachmentShare.attachment_id == id,
        AttachmentShare.status == "active"
    )
    if share_id:
        s_stmt = s_stmt.where(AttachmentShare.id == share_id)
    elif recipient_user_id:
        s_stmt = s_stmt.where(AttachmentShare.shared_with == recipient_user_id)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide recipient_user_id or share_id.")

    s_res = await db.execute(s_stmt)
    shares = s_res.scalars().all()
    for s in shares:
        s.status = "revoked"

    await db.commit()
    return {"status": "success", "message": "Share revoked."}

@router.post("/{id}/promote-to-document", status_code=status.HTTP_201_CREATED)
@router.post("/{id}/add-to-documents", status_code=status.HTTP_201_CREATED)
async def promote_file_to_document(
    id: UUID,
    payload: Optional[PromoteFilePayload] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Attachment).where(Attachment.id == id, Attachment.status == "active")
    res = await db.execute(stmt)
    att = res.scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared file not found.")

    await verify_file_access(db, att, current_user.id)

    # Resolve target workspace
    target_ws_id = (payload.workspace_id if payload else None) or att.workspace_id
    if not target_ws_id:
        from ..workspace.models import Workspace
        ws_stmt = select(Workspace.id).where(
            Workspace.organization_id == att.organization_id
        ).order_by(Workspace.created_at.asc()).limit(1)
        ws_res = await db.execute(ws_stmt)
        target_ws_id = ws_res.scalar_one_or_none()
        if not target_ws_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No workspace found to add document to.")

    # Read binary bytes from storage
    try:
        file_bytes = await default_storage_provider.get_file(att.storage_path)
    except Exception as e:
        logger.exception(f"Failed to read file from storage for document promotion: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load file contents.")

    from ..documents.service import DocumentService
    doc_service = DocumentService(db)

    title = (payload.title if payload else None) or att.original_filename
    project_id = payload.project_id if payload else None

    promoted_doc = await doc_service.upload_document(
        file_content=file_bytes,
        filename=att.original_filename,
        content_type=att.mime_type or "application/octet-stream",
        org_id=att.organization_id,
        workspace_id=target_ws_id,
        project_id=project_id,
        user_id=current_user.id,
        title=title,
        visibility="private"
    )

    await log_audit_event(db, att.id, current_user.id, "promoted_to_document")
    await db.commit()

    return {
        "status": "success",
        "message": f"'{att.original_filename}' successfully added to Knowledge Documents.",
        "document_id": str(promoted_doc.id),
        "title": promoted_doc.title,
        "processing_status": promoted_doc.processing_status,
        "workspace_id": str(target_ws_id)
    }

@router.get("/{id}/download")
async def download_file(
    id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user_from_header_or_query),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Attachment).where(Attachment.id == id, Attachment.status == "active")
    res = await db.execute(stmt)
    att = res.scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found or deleted.")

    await verify_file_access(db, att, current_user.id)

    att.download_count += 1
    await log_audit_event(db, att.id, current_user.id, "download", request)
    await db.commit()

    file_bytes = await default_storage_provider.get_file(att.storage_path)

    from urllib.parse import quote
    safe_filename = quote(att.original_filename)

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=att.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename=\"{safe_filename}\"; filename*=UTF-8''{safe_filename}"}
    )

@router.get("/{id}/preview")
async def preview_file(
    id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user_from_header_or_query),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Attachment).where(Attachment.id == id)
    res = await db.execute(stmt)
    att = res.scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File metadata not found.")

    await verify_file_access(db, att, current_user.id)

    try:
        file_bytes = await default_storage_provider.get_file(att.storage_path)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File binary not found on storage server.")
    except Exception as e:
        logger.exception(f"Error reading file for preview: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Storage read error.")

    await log_audit_event(db, att.id, current_user.id, "preview", request)
    await db.commit()

    content_type = att.mime_type
    ext = att.original_filename.split('.').pop().lower()
    if "pdf" in content_type or ext == "pdf":
        content_type = "application/pdf"
    elif (
        content_type.startswith("text/") or
        "json" in content_type or
        "javascript" in content_type or
        "python" in content_type or
        "typescript" in content_type
    ):
        content_type = f"{content_type}; charset=utf-8"

    from urllib.parse import quote
    safe_filename = quote(att.original_filename)

    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{safe_filename}"',
            "Accept-Ranges": "bytes"
        }
    )

@router.patch("/{id}", response_model=FileResponse)
async def update_file(
    id: UUID,
    payload: FileUpdatePayload,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Attachment, User).join(
        User, Attachment.uploaded_by == User.id
    ).where(Attachment.id == id)
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    att, uploader = row
    await verify_file_access(db, att, current_user.id)

    if payload.original_filename is not None and payload.original_filename.strip():
        att.original_filename = payload.original_filename.strip()
        await log_audit_event(db, att.id, current_user.id, "rename", request)

    if payload.folder_id is not None:
        att.folder_id = payload.folder_id
        await log_audit_event(db, att.id, current_user.id, "move", request)

    att.updated_at = datetime.utcnow()
    await db.commit()

    return FileResponse(
        id=att.id,
        organization_id=att.organization_id,
        workspace_id=att.workspace_id,
        folder_id=att.folder_id,
        conversation_id=att.conversation_id,
        message_id=att.message_id,
        uploaded_by=att.uploaded_by,
        uploader_name=uploader.full_name,
        original_filename=att.original_filename,
        storage_filename=att.storage_filename,
        mime_type=att.mime_type,
        file_size=att.file_size,
        checksum=att.checksum,
        storage_path=att.storage_path,
        preview_url=f"/api/v1/files/{att.id}/preview",
        download_url=f"/api/v1/files/{att.id}/download",
        version=att.version,
        status=att.status,
        processing_status=att.processing_status or "ready",
        scan_status="Safe",
        download_count=att.download_count,
        created_at=att.created_at,
        updated_at=att.updated_at
    )

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def soft_delete_file(
    id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Attachment).where(Attachment.id == id)
    res = await db.execute(stmt)
    att = res.scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    await verify_file_access(db, att, current_user.id)

    att.status = "deleted"
    att.deleted_at = datetime.utcnow()

    await log_audit_event(db, att.id, current_user.id, "delete", request)

    try:
        dash_service = DashboardService(db)
        await dash_service.refresh_dashboard(current_user.id, att.organization_id)
    except Exception:
        pass

    await db.commit()

    return {"status": "success", "message": "File soft deleted successfully"}

@router.post("/{id}/restore", status_code=status.HTTP_200_OK)
async def restore_file(
    id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Attachment).where(Attachment.id == id)
    res = await db.execute(stmt)
    att = res.scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    await verify_file_access(db, att, current_user.id)

    att.status = "active"
    att.deleted_at = None

    await log_audit_event(db, att.id, current_user.id, "restore", request)

    try:
        dash_service = DashboardService(db)
        await dash_service.refresh_dashboard(current_user.id, att.organization_id)
    except Exception:
        pass

    await db.commit()

    return {"status": "success", "message": "File restored successfully"}

# ==============================================================================
# PHASE 2 VERSION HISTORY & AUDIT LOG SUB-ROUTES
# ==============================================================================

@router.get("/{id}/versions", response_model=List[AttachmentVersionResponse])
async def list_file_versions(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Attachment).where(Attachment.id == id)
    att = (await db.execute(stmt)).scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    await verify_file_access(db, att, current_user.id)

    v_stmt = select(AttachmentVersion, User).join(
        User, AttachmentVersion.created_by == User.id
    ).where(
        AttachmentVersion.attachment_id == id
    ).order_by(desc(AttachmentVersion.version_number))

    res = await db.execute(v_stmt)
    result = []
    for ver, creator in res.all():
        result.append(AttachmentVersionResponse(
            id=ver.id,
            attachment_id=ver.attachment_id,
            version_number=ver.version_number,
            storage_filename=ver.storage_filename,
            file_size=ver.file_size,
            checksum=ver.checksum,
            created_by=ver.created_by,
            creator_name=creator.full_name,
            created_at=ver.created_at
        ))
    return result

@router.post("/{id}/versions", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_new_file_version(
    id: UUID,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Attachment, User).join(User, Attachment.uploaded_by == User.id).where(Attachment.id == id)
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    att, uploader = row
    await verify_file_access(db, att, current_user.id)

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File exceeds 50 MB.")

    checksum = hashlib.sha256(file_bytes).hexdigest()
    storage_filename, relative_path = await default_storage_provider.save_file(file_bytes, file.filename or att.original_filename)

    next_version = att.version + 1
    att.version = next_version
    att.storage_filename = storage_filename
    att.file_size = len(file_bytes)
    att.checksum = checksum
    att.storage_path = relative_path
    att.updated_at = datetime.utcnow()

    now = datetime.utcnow()
    version_entry = AttachmentVersion(
        id=uuid4(),
        attachment_id=att.id,
        version_number=next_version,
        storage_filename=storage_filename,
        file_size=len(file_bytes),
        checksum=checksum,
        storage_path=relative_path,
        created_by=current_user.id,
        created_at=now,
        updated_at=now
    )
    db.add(version_entry)

    await log_audit_event(db, att.id, current_user.id, "version_upload", request)
    await db.commit()

    return FileResponse(
        id=att.id,
        organization_id=att.organization_id,
        workspace_id=att.workspace_id,
        folder_id=att.folder_id,
        conversation_id=att.conversation_id,
        message_id=att.message_id,
        uploaded_by=att.uploaded_by,
        uploader_name=uploader.full_name,
        original_filename=att.original_filename,
        storage_filename=att.storage_filename,
        mime_type=att.mime_type,
        file_size=att.file_size,
        checksum=att.checksum,
        storage_path=att.storage_path,
        preview_url=f"/api/v1/files/{att.id}/preview",
        download_url=f"/api/v1/files/{att.id}/download",
        version=att.version,
        status=att.status,
        processing_status=att.processing_status or "ready",
        scan_status="Safe",
        download_count=att.download_count,
        created_at=att.created_at,
        updated_at=att.updated_at
    )

@router.post("/{id}/versions/{version_number}/restore", response_model=FileResponse)
async def restore_file_version(
    id: UUID,
    version_number: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Attachment, User).join(User, Attachment.uploaded_by == User.id).where(Attachment.id == id)
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    att, uploader = row
    await verify_file_access(db, att, current_user.id)

    v_stmt = select(AttachmentVersion).where(
        AttachmentVersion.attachment_id == id,
        AttachmentVersion.version_number == version_number
    )
    v_res = await db.execute(v_stmt)
    ver = v_res.scalar_one_or_none()
    if not ver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Version {version_number} not found.")

    att.storage_filename = ver.storage_filename
    att.file_size = ver.file_size
    att.checksum = ver.checksum
    att.storage_path = ver.storage_path
    att.version = version_number
    att.updated_at = datetime.utcnow()

    await log_audit_event(db, att.id, current_user.id, "version_restore", request)
    await db.commit()

    return FileResponse(
        id=att.id,
        organization_id=att.organization_id,
        workspace_id=att.workspace_id,
        folder_id=att.folder_id,
        conversation_id=att.conversation_id,
        message_id=att.message_id,
        uploaded_by=att.uploaded_by,
        uploader_name=uploader.full_name,
        original_filename=att.original_filename,
        storage_filename=att.storage_filename,
        mime_type=att.mime_type,
        file_size=att.file_size,
        checksum=att.checksum,
        storage_path=att.storage_path,
        preview_url=f"/api/v1/files/{att.id}/preview",
        download_url=f"/api/v1/files/{att.id}/download",
        version=att.version,
        status=att.status,
        processing_status=att.processing_status or "ready",
        scan_status="Safe",
        download_count=att.download_count,
        created_at=att.created_at,
        updated_at=att.updated_at
    )

@router.get("/{id}/versions/{version_number}/download")
async def download_file_version(
    id: UUID,
    version_number: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Attachment).where(Attachment.id == id)
    att = (await db.execute(stmt)).scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    await verify_file_access(db, att, current_user.id)

    v_stmt = select(AttachmentVersion).where(
        AttachmentVersion.attachment_id == id,
        AttachmentVersion.version_number == version_number
    )
    ver = (await db.execute(v_stmt)).scalar_one_or_none()
    if not ver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Version {version_number} not found.")

    await log_audit_event(db, att.id, current_user.id, "version_download", request)
    await db.commit()

    file_bytes = await default_storage_provider.get_file(ver.storage_path)

    from urllib.parse import quote
    safe_filename = quote(f"v{version_number}_{att.original_filename}")

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=att.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'}
    )

@router.get("/{id}/audit", response_model=List[AttachmentAccessLogResponse])
async def get_file_audit_logs(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Attachment).where(Attachment.id == id)
    att = (await db.execute(stmt)).scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    await verify_file_access(db, att, current_user.id)

    log_stmt = select(AttachmentAccessLog, User).join(
        User, AttachmentAccessLog.user_id == User.id
    ).where(
        AttachmentAccessLog.attachment_id == id
    ).order_by(desc(AttachmentAccessLog.accessed_at))

    res = await db.execute(log_stmt)
    result = []
    for log_item, user_item in res.all():
        result.append(AttachmentAccessLogResponse(
            id=log_item.id,
            attachment_id=log_item.attachment_id,
            user_id=log_item.user_id,
            user_name=user_item.full_name,
            action=log_item.action,
            ip_address=log_item.ip_address,
            accessed_at=log_item.accessed_at
        ))
    return result



