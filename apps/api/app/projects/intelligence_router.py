from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .intelligence_service import ProjectIntelligenceService

router = APIRouter(prefix="/projects", tags=["Project Intelligence"])

class HealthSchema(BaseModel):
    status: str
    explanation: str
    overdue_count: int
    blocked_count: int

class TaskSummarySchema(BaseModel):
    total: int
    open: int
    in_progress: int
    blocked: int
    overdue: int
    completed: int

class DecisionItemSchema(BaseModel):
    id: str
    content: str
    created_at: str

class ChangeItemSchema(BaseModel):
    id: str
    event_type: str
    title: str
    description: str
    occurred_at: str

class ProjectIntelligenceResponse(BaseModel):
    project_id: str
    name: str
    description: Optional[str] = None
    status: str
    health: HealthSchema
    current_state: str
    task_summary: TaskSummarySchema
    key_decisions: List[DecisionItemSchema]
    recent_changes: List[ChangeItemSchema]
    open_questions: List[Dict[str, Any]]
    conflicts: List[Dict[str, Any]]

@router.get("/{project_id}/intelligence", response_model=ProjectIntelligenceResponse, status_code=status.HTTP_200_OK)
async def get_project_intelligence(
    project_id: str,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve comprehensive project intelligence, health signals, and task/decision

    summaries.

    """
    try:
        p_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project UUID format")

    service = ProjectIntelligenceService(db)
    res = await service.get_project_intelligence(
        project_id=p_uuid,
        organization_id=org_id,
        user=current_user
    )
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.get("/{project_id}/health", response_model=HealthSchema, status_code=status.HTTP_200_OK)
async def get_project_health(
    project_id: str,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve derived project health badge and explanation."""
    try:
        p_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project UUID format")

    service = ProjectIntelligenceService(db)
    res = await service.get_project_intelligence(
        project_id=p_uuid,
        organization_id=org_id,
        user=current_user
    )
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res["health"]
