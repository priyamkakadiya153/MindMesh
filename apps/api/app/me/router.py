from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .service import UserContextService

router = APIRouter(prefix="/me", tags=["Personal User Context"])

class ActivityRecordRequest(BaseModel):
    event_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    action_metadata: Optional[Dict[str, Any]] = None

@router.get("/context", status_code=status.HTTP_200_OK)
async def get_user_context(
    workspace_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve comprehensive personal context ('My Work') for the current user."""
    ws_uuid = UUID(workspace_id) if workspace_id else None
    service = UserContextService(db)
    return await service.get_user_context(
        user=current_user,
        organization_id=org_id,
        workspace_id=ws_uuid
    )

@router.get("/catch-up", status_code=status.HTTP_200_OK)
async def get_catch_up_summary(
    workspace_id: Optional[str] = None,
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve timeline updates, new decisions, and document changes since the user's last interaction."""
    ws_uuid = UUID(workspace_id) if workspace_id else None
    p_uuid = UUID(project_id) if project_id else None

    service = UserContextService(db)
    return await service.get_catch_up_summary(
        user=current_user,
        organization_id=org_id,
        workspace_id=ws_uuid,
        project_id=p_uuid
    )

@router.post("/activity", status_code=status.HTTP_201_CREATED)
async def record_activity(
    req: ActivityRecordRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Record an explicit knowledge interaction log."""
    ws_uuid = UUID(req.workspace_id) if req.workspace_id else None
    p_uuid = UUID(req.project_id) if req.project_id else None
    ent_uuid = UUID(req.entity_id) if req.entity_id else None

    service = UserContextService(db)
    log = await service.record_user_activity(
        user=current_user,
        organization_id=org_id,
        event_type=req.event_type,
        entity_type=req.entity_type,
        entity_id=ent_uuid,
        workspace_id=ws_uuid,
        project_id=p_uuid,
        action_metadata=req.action_metadata
    )
    return {"message": "Activity recorded successfully", "id": str(log.id)}
