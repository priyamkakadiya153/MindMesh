from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .knowledge_quality_service import KnowledgeQualityService

router = APIRouter(prefix="/quality", tags=["Knowledge Stewardship, Quality & Continuous Maintenance"])

class DismissQualityIssueRequest(BaseModel):
    reason: Optional[str] = None

class AssignOwnerRequest(BaseModel):
    entity_id: str
    owner_id: str

class MergeDuplicatesRequest(BaseModel):
    primary_entity_id: str
    secondary_entity_id: str

class KeepSeparateRequest(BaseModel):
    issue_id: str

@router.get("/issues", status_code=status.HTTP_200_OK)
async def get_quality_issues(
    type_filter: str = Query("ALL"),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve detected quality issues."""
    service = KnowledgeQualityService(db)
    return await service.get_quality_issues(organization_id=org_id, type_filter=type_filter)

@router.post("/scan", status_code=status.HTTP_200_OK)
async def run_quality_scan(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Perform read-only quality scan across authorized entities."""
    p_uuid = None
    if project_id:
        try:
            p_uuid = UUID(project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = KnowledgeQualityService(db)
    return await service.run_quality_scan(organization_id=org_id, project_id=p_uuid, user=current_user)

@router.post("/issues/{issue_id}/resolve", status_code=status.HTTP_200_OK)
async def resolve_issue(
    issue_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Mark a quality issue as resolved."""
    service = KnowledgeQualityService(db)
    return await service.resolve_issue(issue_id=issue_id, user=current_user)

@router.post("/issues/{issue_id}/dismiss", status_code=status.HTTP_200_OK)
async def dismiss_issue(
    issue_id: str,
    req: DismissQualityIssueRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Dismiss a quality issue with feedback reason."""
    service = KnowledgeQualityService(db)
    return await service.dismiss_issue(issue_id=issue_id, reason=req.reason, user=current_user)

@router.post("/assign-owner", status_code=status.HTTP_200_OK)
async def assign_owner(
    req: AssignOwnerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Assign an owner to unowned knowledge."""
    service = KnowledgeQualityService(db)
    return await service.assign_owner(entity_id=req.entity_id, owner_id=req.owner_id, user=current_user)

@router.post("/merge-duplicates", status_code=status.HTTP_200_OK)
async def merge_duplicates(
    req: MergeDuplicatesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Safely merge duplicate entities into a primary target."""
    service = KnowledgeQualityService(db)
    return await service.merge_duplicates(primary_entity_id=req.primary_entity_id, secondary_entity_id=req.secondary_entity_id, user=current_user)

@router.post("/keep-separate", status_code=status.HTTP_200_OK)
async def keep_separate(
    req: KeepSeparateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Explicitly mark duplicate candidate entities as separate."""
    service = KnowledgeQualityService(db)
    return await service.keep_separate(issue_id=req.issue_id, user=current_user)

@router.get("/health", status_code=status.HTTP_200_OK)
async def get_knowledge_health(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Return aggregate health metrics for Organization scope."""
    service = KnowledgeQualityService(db)
    return await service.get_knowledge_health(organization_id=org_id)
