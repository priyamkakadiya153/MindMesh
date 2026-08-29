from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .workspace_service import ProactiveWorkspaceService

router = APIRouter(prefix="/proactive", tags=["Proactive Knowledge Workspace & Intelligent Workflow Orchestration"])

class DismissInsightRequest(BaseModel):
    reason: Optional[str] = None

class SnoozeInsightRequest(BaseModel):
    duration: str = "1d"

class FollowEntityRequest(BaseModel):
    entity_id: str

@router.get("/feed", status_code=status.HTTP_200_OK)
async def get_proactive_feed(
    project_id: Optional[str] = None,
    filter_status: str = Query("UNREAD"),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve evaluated proactive insights feed."""
    p_uuid = None
    if project_id:
        try:
            p_uuid = UUID(project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = ProactiveWorkspaceService(db)
    return await service.get_proactive_feed(user=current_user, organization_id=org_id, project_id=p_uuid, filter_status=filter_status)

@router.post("/insights/{insight_id}/dismiss", status_code=status.HTTP_200_OK)
async def dismiss_insight(
    insight_id: str,
    req: DismissInsightRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Dismiss a proactive insight with optional feedback reason."""
    service = ProactiveWorkspaceService(db)
    return await service.dismiss_insight(insight_id=insight_id, reason=req.reason, user=current_user)

@router.post("/insights/{insight_id}/snooze", status_code=status.HTTP_200_OK)
async def snooze_insight(
    insight_id: str,
    req: SnoozeInsightRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Snooze proactive notifications for a specified duration."""
    service = ProactiveWorkspaceService(db)
    return await service.snooze_insight(insight_id=insight_id, duration=req.duration, user=current_user)

@router.post("/insights/follow", status_code=status.HTTP_200_OK)
async def follow_entity(
    req: FollowEntityRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Subscribe to continuous updates for a specific entity."""
    service = ProactiveWorkspaceService(db)
    return await service.follow_entity(entity_id=req.entity_id, user=current_user)

@router.get("/inbox", status_code=status.HTTP_200_OK)
async def get_inbox(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve user's personalized Intelligence Inbox items."""
    service = ProactiveWorkspaceService(db)
    return await service.get_inbox(user=current_user, organization_id=org_id)

@router.post("/rebuild", status_code=status.HTTP_200_OK)
async def rebuild_proactive_insights(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Idempotently reconstruct proactive insights from primary database records."""
    service = ProactiveWorkspaceService(db)
    return await service.rebuild_proactive_insights(organization_id=org_id)
