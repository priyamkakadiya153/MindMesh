from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .service import KnowledgeOperationsService

router = APIRouter(prefix="/operations", tags=["Knowledge Operations & Analytics"])

@router.get("/health", status_code=status.HTTP_200_OK)
async def get_knowledge_health(
    workspace_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve organizational knowledge health counts based on verified database records."""
    ws_uuid = UUID(workspace_id) if workspace_id else None
    service = KnowledgeOperationsService(db)
    return await service.get_knowledge_health(organization_id=org_id, workspace_id=ws_uuid)

@router.get("/coverage", status_code=status.HTTP_200_OK)
async def get_project_coverage(
    workspace_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve project knowledge coverage profiles."""
    ws_uuid = UUID(workspace_id) if workspace_id else None
    service = KnowledgeOperationsService(db)
    return await service.get_project_coverage(organization_id=org_id, workspace_id=ws_uuid)

@router.get("/gaps", status_code=status.HTTP_200_OK)
async def detect_knowledge_gaps(
    workspace_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Detect knowledge gaps and recommendations."""
    ws_uuid = UUID(workspace_id) if workspace_id else None
    service = KnowledgeOperationsService(db)
    return await service.detect_knowledge_gaps(organization_id=org_id, workspace_id=ws_uuid)

@router.post("/projects/{project_id}/handoff", status_code=status.HTTP_200_OK)
async def generate_project_handoff(
    project_id: str,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate a grounded, source-backed Project Knowledge Brief for handoffs."""
    try:
        p_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project UUID")

    service = KnowledgeOperationsService(db)
    res = await service.generate_project_handoff(project_id=p_uuid, user=current_user, organization_id=org_id)
    if not res:
        raise HTTPException(status_code=404, detail="Project not found or access denied")
    return res
