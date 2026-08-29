from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .service import TimelineService
from .backfill import TimelineBackfillService

router = APIRouter(prefix="/timeline", tags=["Knowledge Timeline"])

class TimelineEventItem(BaseModel):
    id: str
    organization_id: str
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    event_type: str
    importance: str
    title: str
    description: Optional[str] = None
    source_type: str
    source_id: str
    occurred_at: Optional[str] = None
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = {}
    deep_link: Optional[str] = None

class TimelineListResponse(BaseModel):
    events: List[TimelineEventItem]
    total_count: int
    page: int
    limit: int
    total_pages: int

class BackfillResponse(BaseModel):
    success: bool
    stats: Dict[str, Any]

@router.get("", response_model=TimelineListResponse, status_code=status.HTTP_200_OK)
@router.get("/", response_model=TimelineListResponse, status_code=status.HTTP_200_OK)
async def get_timeline_events(
    workspace_id: Optional[str] = Query(None, description="Workspace UUID filter"),
    project_id: Optional[str] = Query(None, description="Project UUID filter"),
    event_type: Optional[str] = Query(None, description="Event type filter"),
    importance: Optional[str] = Query(None, description="Importance filter: HIGH, MEDIUM, LOW"),
    q: Optional[str] = Query(None, description="Search query string"),
    date_from: Optional[datetime] = Query(None, description="Start date filter"),
    date_to: Optional[datetime] = Query(None, description="End date filter"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(30, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve chronologically ordered Knowledge Timeline events with RBAC

    and project/workspace security filtering.

    """
    ws_uuid = UUID(workspace_id) if workspace_id and workspace_id != "all" else None
    proj_uuid = UUID(project_id) if project_id and project_id != "all" else None

    service = TimelineService(db)
    res = await service.get_timeline_events(
        user=current_user,
        organization_id=org_id,
        workspace_id=ws_uuid,
        project_id=proj_uuid,
        event_type=event_type,
        importance=importance,
        search_query=q,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit
    )
    return res

@router.get("/evolution", status_code=status.HTTP_200_OK)
async def get_knowledge_evolution(
    query: str = Query(..., min_length=2, description="Topic or decision query"),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve chronological decision and knowledge evolution chain for a query."""
    service = TimelineService(db)
    evolution = await service.get_knowledge_evolution(
        organization_id=org_id,
        query=query,
        user_id=current_user.id
    )
    return {"query": query, "evolution": evolution}

@router.post("/backfill", response_model=BackfillResponse, status_code=status.HTTP_200_OK)
async def trigger_timeline_backfill(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Idempotently backfill historical documents, messages, tasks, and projects

    into timeline events.

    """
    backfill_service = TimelineBackfillService(db)
    stats = await backfill_service.run_backfill(organization_id=org_id)
    return {"success": True, "stats": stats}
