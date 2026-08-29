from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .knowledge_maintenance_service import KnowledgeMaintenanceService

router = APIRouter(prefix="/knowledge-maintenance", tags=["Autonomous Knowledge Maintenance, Contextual Memory & Self-Improving Organizational Intelligence"])

class MergePreviewRequest(BaseModel):
    source_a_id: str
    source_b_id: str

class RevalidateKnowledgeRequest(BaseModel):
    entity_id: str
    revalidation_state: str = "STILL_VALID"

class ContextSearchRequest(BaseModel):
    query: str
    scope_context: str = "PROJECT_A"

@router.get("/review-queue", status_code=status.HTTP_200_OK)
async def get_review_queue(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve impact-aware Knowledge Review Queue."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = KnowledgeMaintenanceService(db)
    return await service.get_review_queue(organization_id=org_id, user=current_user)

@router.post("/canonical-candidates", status_code=status.HTTP_200_OK)
async def scan_canonical_candidates(
    project_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Scan project for canonical document candidates."""
    try:
        p_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = KnowledgeMaintenanceService(db)
    return await service.scan_canonical_candidates(project_id=p_uuid, user=current_user)

@router.post("/merge-preview", status_code=status.HTTP_200_OK)
async def generate_merge_preview(
    req: MergePreviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate side-by-side merge preview."""
    service = KnowledgeMaintenanceService(db)
    return await service.generate_merge_preview(source_a_id=req.source_a_id, source_b_id=req.source_b_id, user=current_user)

@router.post("/revalidate", status_code=status.HTTP_200_OK)
async def revalidate_knowledge(
    req: RevalidateKnowledgeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Revalidate knowledge freshness timestamp."""
    service = KnowledgeMaintenanceService(db)
    return await service.revalidate_knowledge(entity_id=req.entity_id, revalidation_state=req.revalidation_state, user=current_user)

@router.post("/self-heal-index", status_code=status.HTTP_200_OK)
async def self_heal_index(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Automatically repair broken derived search indices."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = KnowledgeMaintenanceService(db)
    return await service.self_heal_index(organization_id=org_id, user=current_user)

@router.post("/context-search", status_code=status.HTTP_200_OK)
async def context_aware_search(
    req: ContextSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Perform context-aware memory retrieval."""
    service = KnowledgeMaintenanceService(db)
    return await service.context_aware_search(query=req.query, scope_context=req.scope_context, user=current_user)

@router.get("/digest", status_code=status.HTTP_200_OK)
async def get_maintenance_digest(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve maintenance summary digest."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = KnowledgeMaintenanceService(db)
    return await service.get_maintenance_digest(organization_id=org_id, user=current_user)
