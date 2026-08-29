from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .trust_service import KnowledgeGovernanceTrustService

router = APIRouter(prefix="/governance/trust", tags=["Knowledge Governance & Trust Layer"])

class ConfirmExtractionRequest(BaseModel):
    review_item_id: str
    edited_title: Optional[str] = None
    edited_description: Optional[str] = None

class RejectExtractionRequest(BaseModel):
    review_item_id: str
    reason: Optional[str] = None

class ResolveConflictRequest(BaseModel):
    conflict_id: str
    winning_source_id: str
    resolution_notes: Optional[str] = None

class SetSourceOfTruthRequest(BaseModel):
    project_id: str
    entity_id: str
    entity_title: str

@router.get("/review-queue", status_code=status.HTTP_200_OK)
async def get_review_queue(
    workspace_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve review queue items and active conflicts for governance."""
    ws_uuid = UUID(workspace_id) if workspace_id else None
    p_uuid = UUID(project_id) if project_id else None
    service = KnowledgeGovernanceTrustService(db)
    return await service.get_review_queue(organization_id=org_id, workspace_id=ws_uuid, project_id=p_uuid)

@router.post("/confirm", status_code=status.HTTP_200_OK)
async def confirm_extraction(
    req: ConfirmExtractionRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Confirm or edit an AI-extracted knowledge item."""
    service = KnowledgeGovernanceTrustService(db)
    return await service.confirm_ai_extraction(
        user=current_user,
        organization_id=org_id,
        review_item_id=req.review_item_id,
        edited_title=req.edited_title,
        edited_description=req.edited_description
    )

@router.post("/reject", status_code=status.HTTP_200_OK)
async def reject_extraction(
    req: RejectExtractionRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Reject an AI extraction non-destructively."""
    service = KnowledgeGovernanceTrustService(db)
    return await service.reject_ai_extraction(
        user=current_user,
        organization_id=org_id,
        review_item_id=req.review_item_id,
        reason=req.reason
    )

@router.post("/resolve-conflict", status_code=status.HTTP_200_OK)
async def resolve_conflict(
    req: ResolveConflictRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Resolve a knowledge conflict between contradictory sources."""
    service = KnowledgeGovernanceTrustService(db)
    return await service.resolve_conflict(
        user=current_user,
        organization_id=org_id,
        conflict_id=req.conflict_id,
        winning_source_id=req.winning_source_id,
        resolution_notes=req.resolution_notes
    )

@router.post("/set-source-of-truth", status_code=status.HTTP_200_OK)
async def set_source_of_truth(
    req: SetSourceOfTruthRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Designate an authoritative document/decision as Source of Truth."""
    try:
        p_uuid = UUID(req.project_id)
        e_uuid = UUID(req.entity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    service = KnowledgeGovernanceTrustService(db)
    return await service.set_source_of_truth(
        user=current_user,
        organization_id=org_id,
        project_id=p_uuid,
        entity_id=e_uuid,
        entity_title=req.entity_title
    )

@router.get("/audit-log", status_code=status.HTTP_200_OK)
async def get_governance_audit_log(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve governance audit log history."""
    service = KnowledgeGovernanceTrustService(db)
    return await service.get_governance_audit_log(organization_id=org_id)
