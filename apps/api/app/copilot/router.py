from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .grounded_service import GroundedAnswerEngineService

router = APIRouter(prefix="/copilot", tags=["Knowledge Copilot & Grounded Q&A Engine"])

class AskQuestionRequest(BaseModel):
    question: str
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None

class ProjectBriefRequest(BaseModel):
    project_id: str

@router.post("/ask", status_code=status.HTTP_200_OK)
async def ask_mindmesh(
    req: AskQuestionRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Execute grounded Q&A with evidence selection, conflict warnings, exact citations, and follow-ups."""
    ws_uuid = UUID(req.workspace_id) if req.workspace_id else None
    p_uuid = UUID(req.project_id) if req.project_id else None

    service = GroundedAnswerEngineService(db)
    return await service.ask_mindmesh(
        question=req.question,
        user=current_user,
        organization_id=org_id,
        workspace_id=ws_uuid,
        project_id=p_uuid
    )

@router.post("/project-brief", status_code=status.HTTP_200_OK)
async def generate_project_brief(
    req: ProjectBriefRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate flagship comprehensive project brief using current organizational memory."""
    try:
        p_uuid = UUID(req.project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project UUID format")

    service = GroundedAnswerEngineService(db)
    try:
        return await service.generate_project_brief(project_id=p_uuid, user=current_user, organization_id=org_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
