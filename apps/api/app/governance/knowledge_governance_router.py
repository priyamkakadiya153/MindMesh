from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .knowledge_governance_service import KnowledgeGovernanceService

router = APIRouter(prefix="/governance", tags=["Knowledge Governance, Trust & Organizational Control"])

class SubmitReviewRequest(BaseModel):
    entity_id: str
    entity_type: str
    reviewer_id: Optional[str] = None

class ApproveVersionRequest(BaseModel):
    entity_id: str
    version: str

class RejectVersionRequest(BaseModel):
    entity_id: str
    reason: str

class RequestChangesRequest(BaseModel):
    entity_id: str
    required_changes: str

class ResolveConflictRequest(BaseModel):
    conflict_id: str
    resolution_strategy: str
    current_entity_id: str
    superseded_entity_id: str

class ArchiveEntityRequest(BaseModel):
    entity_id: str

class RestoreVersionRequest(BaseModel):
    entity_id: str
    target_version: str

@router.post("/submit-review", status_code=status.HTTP_200_OK)
async def submit_for_review(
    req: SubmitReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Transition draft entity to Under Review."""
    service = KnowledgeGovernanceService(db)
    return await service.submit_for_review(entity_id=req.entity_id, entity_type=req.entity_type, reviewer_id=req.reviewer_id, user=current_user)

@router.post("/approve", status_code=status.HTTP_200_OK)
async def approve_version(
    req: ApproveVersionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Approve a specific version and publish governed knowledge."""
    service = KnowledgeGovernanceService(db)
    return await service.approve_version(entity_id=req.entity_id, version=req.version, user=current_user)

@router.post("/reject", status_code=status.HTTP_200_OK)
async def reject_version(
    req: RejectVersionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Reject submission with mandatory feedback reason."""
    service = KnowledgeGovernanceService(db)
    return await service.reject_version(entity_id=req.entity_id, reason=req.reason, user=current_user)

@router.post("/request-changes", status_code=status.HTTP_200_OK)
async def request_changes(
    req: RequestChangesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Request specific modifications from author."""
    service = KnowledgeGovernanceService(db)
    return await service.request_changes(entity_id=req.entity_id, required_changes=req.required_changes, user=current_user)

@router.get("/queue", status_code=status.HTTP_200_OK)
async def get_review_queue(
    status_filter: str = Query("ALL"),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve active items in governance review queue."""
    service = KnowledgeGovernanceService(db)
    return await service.get_review_queue(organization_id=org_id, status_filter=status_filter)

@router.post("/resolve-conflict", status_code=status.HTTP_200_OK)
async def resolve_conflict(
    req: ResolveConflictRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Manage human conflict resolution."""
    service = KnowledgeGovernanceService(db)
    return await service.resolve_conflict(
        conflict_id=req.conflict_id,
        resolution_strategy=req.resolution_strategy,
        current_entity_id=req.current_entity_id,
        superseded_entity_id=req.superseded_entity_id,
        user=current_user
    )

@router.post("/archive", status_code=status.HTTP_200_OK)
async def archive_entity(
    req: ArchiveEntityRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Archive content while retaining historical audit traceability."""
    service = KnowledgeGovernanceService(db)
    return await service.archive_entity(entity_id=req.entity_id, user=current_user)

@router.post("/restore", status_code=status.HTTP_200_OK)
async def restore_version(
    req: RestoreVersionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Restore previous historical version by creating a new version."""
    service = KnowledgeGovernanceService(db)
    return await service.restore_version(entity_id=req.entity_id, target_version=req.target_version, user=current_user)

@router.get("/audit-log", status_code=status.HTTP_200_OK)
async def get_audit_log(
    entity_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Query immutable governance audit log records."""
    service = KnowledgeGovernanceService(db)
    return await service.get_audit_log(entity_id=entity_id)
