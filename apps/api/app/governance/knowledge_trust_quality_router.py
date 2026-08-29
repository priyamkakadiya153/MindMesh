from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .knowledge_trust_quality_service import KnowledgeTrustQualityService

router = APIRouter(prefix="/trust-quality", tags=["Trust, Knowledge Governance & Intelligence Quality System"])

class VerifyRequest(BaseModel):
    entity_id: str
    verification_status: str
    reason: str

class ResolveConflictRequest(BaseModel):
    conflict_id: str
    resolution_strategy: str
    reason: str

class ConfirmAIRequest(BaseModel):
    entity_id: str

class RevalidateRequest(BaseModel):
    entity_id: str

@router.get("/provenance/{entity_id}", status_code=status.HTTP_200_OK)
async def get_provenance_detail(
    entity_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves exact provenance, source authority, verification state, and lineage chain."""
    service = KnowledgeTrustQualityService(db)
    return await service.get_provenance_detail(entity_id=entity_id, user=current_user)

@router.post("/verify", status_code=status.HTTP_200_OK)
async def update_verification_state(
    req: VerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Updates verification status with reviewer audit log."""
    service = KnowledgeTrustQualityService(db)
    return await service.update_verification_state(entity_id=req.entity_id, verification_status=req.verification_status, reason=req.reason, user=current_user)

@router.get("/conflicts", status_code=status.HTTP_200_OK)
async def detect_and_manage_conflicts(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Identifies contradictory claims across documents/decisions."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = KnowledgeTrustQualityService(db)
    return await service.detect_and_manage_conflicts(organization_id=org_id, user=current_user)

@router.post("/resolve-conflict", status_code=status.HTTP_200_OK)
async def resolve_conflict(
    req: ResolveConflictRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Resolves conflict explicitly."""
    service = KnowledgeTrustQualityService(db)
    return await service.resolve_conflict(conflict_id=req.conflict_id, resolution_strategy=req.resolution_strategy, reason=req.reason, user=current_user)

@router.post("/confirm-ai", status_code=status.HTTP_200_OK)
async def confirm_ai_suggestion(
    req: ConfirmAIRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Records human confirmation or modification of AI-generated content."""
    service = KnowledgeTrustQualityService(db)
    return await service.confirm_ai_suggestion(entity_id=req.entity_id, user=current_user)

@router.get("/review-queue", status_code=status.HTTP_200_OK)
async def get_review_queue(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Aggregates items needing human review categorized by priority."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = KnowledgeTrustQualityService(db)
    return await service.get_review_queue(organization_id=org_id, user=current_user)

@router.post("/revalidate", status_code=status.HTTP_200_OK)
async def revalidate_ai_result(
    req: RevalidateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Revalidates AI outputs against current evidence."""
    service = KnowledgeTrustQualityService(db)
    return await service.revalidate_ai_result(entity_id=req.entity_id, user=current_user)

@router.get("/audit-log", status_code=status.HTTP_200_OK)
async def get_quality_audit_log(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves immutable audit logs."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = KnowledgeTrustQualityService(db)
    return await service.get_quality_audit_log(organization_id=org_id, user=current_user)
