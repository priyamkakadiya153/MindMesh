from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .service import ConversationIntelligenceService

router = APIRouter(prefix="/conversations", tags=["Conversation Intelligence"])

class PromoteItemRequest(BaseModel):
    item_id: str
    project_id: str

class GenerateMeetingNotesRequest(BaseModel):
    title: Optional[str] = "Authentication Deployment Meeting Notes"

@router.post("/{chat_id}/summary", status_code=status.HTTP_200_OK)
async def generate_conversation_summary(
    chat_id: str,
    summary_type: str = Query("QUICK", description="Summary type (QUICK, DETAILED, ACTION)"),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate or retrieve structured conversation summary."""
    try:
        c_uuid = UUID(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chat UUID format")

    service = ConversationIntelligenceService(db)
    try:
        return await service.summarize_conversation(chat_id=c_uuid, summary_type=summary_type, user=current_user, organization_id=org_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{chat_id}/knowledge", status_code=status.HTTP_200_OK)
async def get_conversation_knowledge(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Extract decisions, tasks, questions, and blockers grounded in source messages."""
    try:
        c_uuid = UUID(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chat UUID format")

    service = ConversationIntelligenceService(db)
    try:
        return await service.extract_conversation_knowledge(chat_id=c_uuid, user=current_user, organization_id=org_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{chat_id}/promote", status_code=status.HTTP_200_OK)
async def promote_item_to_project(
    chat_id: str,
    req: PromoteItemRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Promote an extracted item (decision/task) to a shared project entity upon human confirmation."""
    try:
        i_uuid = UUID(req.item_id)
        p_uuid = UUID(req.project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid item or project UUID format")

    service = ConversationIntelligenceService(db)
    try:
        return await service.promote_item_to_project(item_id=i_uuid, project_id=p_uuid, user=current_user, organization_id=org_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{chat_id}/meeting-notes", status_code=status.HTTP_200_OK)
async def generate_meeting_notes(
    chat_id: str,
    req: GenerateMeetingNotesRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate structured meeting notes linking source messages."""
    try:
        c_uuid = UUID(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chat UUID format")

    service = ConversationIntelligenceService(db)
    try:
        return await service.generate_meeting_notes(chat_id=c_uuid, title=req.title or "Meeting Notes")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
