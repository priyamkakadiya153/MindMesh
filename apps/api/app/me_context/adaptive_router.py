from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .adaptive_service import PersonalContextAdaptiveService

router = APIRouter(prefix="/me/context", tags=["Personal Context & Adaptive Intelligence"])

class PinProjectRequest(BaseModel):
    project_id: str

@router.get("", status_code=status.HTTP_200_OK)
async def get_personal_context(
    active_project_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve user's personal context signals."""
    p_uuid = UUID(active_project_id) if active_project_id else None
    service = PersonalContextAdaptiveService(db)
    return await service.get_user_personal_context(user=current_user, organization_id=org_id, active_project_id=p_uuid)

@router.post("/focus", status_code=status.HTTP_200_OK)
async def get_focus_recommendations(
    active_project_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Execute flagship 'What should I focus on?' query."""
    p_uuid = UUID(active_project_id) if active_project_id else None
    service = PersonalContextAdaptiveService(db)
    return await service.get_focus_recommendations(user=current_user, organization_id=org_id, active_project_id=p_uuid)

@router.post("/away-summary", status_code=status.HTTP_200_OK)
async def get_away_summary(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Execute flagship 'What did I miss while away?' query."""
    service = PersonalContextAdaptiveService(db)
    return await service.get_away_summary(user=current_user, organization_id=org_id)

@router.post("/pin", status_code=status.HTTP_200_OK)
async def pin_project(
    req: PinProjectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Pin a project to personal context."""
    try:
        p_uuid = UUID(req.project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project UUID format")

    service = PersonalContextAdaptiveService(db)
    return await service.pin_project(user_id=current_user.id, project_id=p_uuid)

@router.post("/unpin", status_code=status.HTTP_200_OK)
async def unpin_project(
    req: PinProjectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Unpin a project from personal context."""
    try:
        p_uuid = UUID(req.project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project UUID format")

    service = PersonalContextAdaptiveService(db)
    return await service.unpin_project(user_id=current_user.id, project_id=p_uuid)
