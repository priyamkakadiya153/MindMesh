from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .hub_service import KnowledgeHubService

router = APIRouter(prefix="/hub", tags=["Unified Knowledge Hub"])

class KnowledgeCountsSchema(BaseModel):
    documents: int
    decisions: int
    tasks: int
    conversations: int
    projects: int

class KnowledgeItemSchema(BaseModel):
    id: str
    type: str
    title: str
    description: str
    source_type: str
    source_id: str
    timestamp: str
    deep_link: str
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None

class ActivityItemSchema(BaseModel):
    id: str
    event_type: str
    title: str
    description: str
    occurred_at: str
    source_type: str
    source_id: str

class HubOverviewResponse(BaseModel):
    counts: KnowledgeCountsSchema
    recent_knowledge: List[KnowledgeItemSchema]
    recent_activity: List[ActivityItemSchema]

class ProjectKnowledgeOverviewResponse(BaseModel):
    project_id: str
    name: str
    description: Optional[str] = None
    status: str
    counts: Dict[str, int]
    key_decisions: List[str]
    open_tasks: List[str]

@router.get("/overview", response_model=HubOverviewResponse, status_code=status.HTTP_200_OK)
async def get_hub_overview(
    workspace_id: Optional[str] = Query(None, description="Workspace UUID filter"),
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve Unified Knowledge Hub overview with real counts, recent feed, and

    activity.

    """
    ws_uuid = UUID(workspace_id) if workspace_id and workspace_id != "all" else None
    service = KnowledgeHubService(db)
    res = await service.get_hub_overview(
        user=current_user,
        organization_id=org_id,
        workspace_id=ws_uuid,
        limit=limit
    )
    return res

@router.get("/project/{project_id}", response_model=ProjectKnowledgeOverviewResponse, status_code=status.HTTP_200_OK)
async def get_project_knowledge_overview(
    project_id: str,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve connected knowledge overview for a specific project."""
    try:
        p_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project UUID format")

    service = KnowledgeHubService(db)
    res = await service.get_project_knowledge_overview(
        user=current_user,
        organization_id=org_id,
        project_id=p_uuid
    )
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res
