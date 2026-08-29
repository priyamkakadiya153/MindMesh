from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .contextual_assistant_service import ContextualAssistantService

router = APIRouter(prefix="/assistant", tags=["Contextual AI Assistant & Knowledge Copilot"])

class AskQuestionRequest(BaseModel):
    question: str
    context_entity_id: Optional[str] = None
    context_entity_type: Optional[str] = None
    project_id: Optional[str] = None
    selected_sources: Optional[List[str]] = None

class ResearchRequest(BaseModel):
    topic: str
    project_id: Optional[str] = None

class SummarizeRequest(BaseModel):
    entity_type: str
    entity_id: str

class CompareRequest(BaseModel):
    entity_id_a: str
    entity_id_b: str

class ActionPreviewRequest(BaseModel):
    action_type: str
    title: str
    project_id: Optional[str] = None

@router.post("/ask", status_code=status.HTTP_200_OK)
async def ask_assistant(
    req: AskQuestionRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Answer context-aware questions grounded in authorized entity context and search results."""
    p_uuid = None
    if req.project_id:
        try:
            p_uuid = UUID(req.project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = ContextualAssistantService(db)
    return await service.ask(
        question=req.question,
        context_entity_id=req.context_entity_id,
        context_entity_type=req.context_entity_type,
        project_id=p_uuid,
        selected_sources=req.selected_sources,
        user=current_user,
        organization_id=org_id
    )

@router.post("/research", status_code=status.HTTP_200_OK)
async def conduct_research(
    req: ResearchRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Conduct deep topic research across organizational memory."""
    p_uuid = None
    if req.project_id:
        try:
            p_uuid = UUID(req.project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = ContextualAssistantService(db)
    return await service.research(topic=req.topic, project_id=p_uuid, user=current_user, organization_id=org_id)

@router.post("/summarize", status_code=status.HTTP_200_OK)
async def summarize_entity(
    req: SummarizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate structured summary for Projects, Documents, Decisions, Conversations, or Search Results."""
    service = ContextualAssistantService(db)
    return await service.summarize(entity_type=req.entity_type, entity_id=req.entity_id, user=current_user)

@router.post("/compare", status_code=status.HTTP_200_OK)
async def compare_entities(
    req: CompareRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Compare entities or options side-by-side."""
    service = ContextualAssistantService(db)
    return await service.compare(entity_id_a=req.entity_id_a, entity_id_b=req.entity_id_b)

@router.post("/action-preview", status_code=status.HTTP_200_OK)
async def preview_action(
    req: ActionPreviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate action preview object requiring explicit user confirmation."""
    p_uuid = None
    if req.project_id:
        try:
            p_uuid = UUID(req.project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = ContextualAssistantService(db)
    return await service.preview_action(action_type=req.action_type, title=req.title, project_id=p_uuid, user=current_user)
