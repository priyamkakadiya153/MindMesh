from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .anticipatory_service import ProactiveAnticipatoryEngineService

router = APIRouter(prefix="/proactive", tags=["Proactive Knowledge & Anticipatory Intelligence"])

class MarkReadRequest(BaseModel):
    insight_ids: List[str]

class DismissInsightRequest(BaseModel):
    insight_id: str

class UpdatePreferencesRequest(BaseModel):
    preferences: Dict[str, bool]

@router.get("/insights", status_code=status.HTTP_200_OK)
async def get_user_proactive_insights(
    filter_type: str = Query("ALL", description="Filter (ALL, CRITICAL, IMPORTANT, TASK_ASSIGNED, DECISION_UPDATED, BLOCKER_CREATED)"),
    workspace_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve proactive insights and notifications for current user."""
    ws_uuid = UUID(workspace_id) if workspace_id else None
    service = ProactiveAnticipatoryEngineService(db)
    return await service.get_user_proactive_insights(
        user=current_user,
        organization_id=org_id,
        workspace_id=ws_uuid,
        filter_type=filter_type
    )

@router.post("/insights/read", status_code=status.HTTP_200_OK)
async def mark_insights_read(
    req: MarkReadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Mark specified insights as read."""
    service = ProactiveAnticipatoryEngineService(db)
    return await service.mark_insights_read(user_id=current_user.id, insight_ids=req.insight_ids)

@router.post("/insights/dismiss", status_code=status.HTTP_200_OK)
async def dismiss_insight(
    req: DismissInsightRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Dismiss an insight non-destructively without deleting source entity."""
    service = ProactiveAnticipatoryEngineService(db)
    return await service.dismiss_insight(user_id=current_user.id, insight_id=req.insight_id)

@router.post("/preferences", status_code=status.HTTP_200_OK)
async def update_preferences(
    req: UpdatePreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update user notification category preferences."""
    service = ProactiveAnticipatoryEngineService(db)
    return await service.update_user_preferences(user_id=current_user.id, preferences=req.preferences)
