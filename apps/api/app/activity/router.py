from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from ..core.database import get_db_session
from ..authorization.organization_resolver import resolve_organization_id
from .service import ActivityService

router = APIRouter()

@router.get("/")
async def list_activities(
    limit: int = 50,
    offset: int = 0,
    workspace_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
    event_type: Optional[str] = None,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = ActivityService(db)
    activities = await service.list_timeline(
        org_id=org_id,
        limit=limit,
        offset=offset,
        workspace_id=workspace_id,
        project_id=project_id,
        event_type=event_type
    )
    return [
        {
            "id": act.id,
            "organization_id": act.organization_id,
            "workspace_id": act.workspace_id,
            "project_id": act.project_id,
            "user_id": act.user_id,
            "event_type": act.event_type,
            "entity_type": act.entity_type,
            "entity_id": act.entity_id,
            "metadata": act.action_metadata,
            "created_at": act.created_at

        }
        for act in activities
    ]

@router.get("/{id}")
async def get_activity(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = ActivityService(db)
    from sqlalchemy import select
    from .models import ActivityLog
    stmt = select(ActivityLog).where(
        ActivityLog.id == id,
        ActivityLog.organization_id == org_id
    )
    res = await db.execute(stmt)
    act = res.scalar_one_or_none()
    if not act:
        raise HTTPException(status_code=404, detail="Activity log not found")
    return {
        "id": act.id,
        "organization_id": act.organization_id,
        "workspace_id": act.workspace_id,
        "project_id": act.project_id,
        "user_id": act.user_id,
        "event_type": act.event_type,
        "entity_type": act.entity_type,
        "entity_id": act.entity_id,
        "metadata": act.action_metadata,
        "created_at": act.created_at

    }
