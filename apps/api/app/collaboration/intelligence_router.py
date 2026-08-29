from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .intelligence_service import CollaborativeIntelligenceService

router = APIRouter(prefix="/collaboration", tags=["Collaborative Intelligence & Team Memory"])

class ConfirmSuggestionRequest(BaseModel):
    suggestion_id: str

class CreateReviewRoomRequest(BaseModel):
    title: str
    conflicting_sources: List[str]

class ResolveReviewRequest(BaseModel):
    room_id: str
    resolution_notes: str

class SpecializedFileRequest(BaseModel):
    filename: str
    mime_type: str

@router.get("/conversation-context/{conversation_id}", status_code=status.HTTP_200_OK)
async def get_conversation_context(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve enriched collaboration context for a conversation."""
    try:
        c_uuid = UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation_id UUID format")

    service = CollaborativeIntelligenceService(db)
    return await service.get_conversation_context(conversation_id=c_uuid, user=current_user)

@router.post("/detect-suggestions", status_code=status.HTTP_200_OK)
async def detect_suggestions(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Scan group discussions to extract Potential Decisions, Tasks, and Open Questions."""
    try:
        c_uuid = UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation_id UUID format")

    service = CollaborativeIntelligenceService(db)
    return await service.detect_suggestions_from_conversation(conversation_id=c_uuid, messages=[])

@router.post("/confirm-decision", status_code=status.HTTP_200_OK)
async def confirm_decision(
    req: ConfirmSuggestionRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Promote a suggested decision to official status."""
    service = CollaborativeIntelligenceService(db)
    return await service.confirm_decision(suggestion_id=req.suggestion_id, user=current_user, organization_id=org_id)

@router.post("/confirm-task", status_code=status.HTTP_200_OK)
async def confirm_task(
    req: ConfirmSuggestionRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Promote a suggested task to official project task."""
    service = CollaborativeIntelligenceService(db)
    return await service.confirm_task(suggestion_id=req.suggestion_id, user=current_user, organization_id=org_id)

@router.get("/team-digest", status_code=status.HTTP_200_OK)
async def get_team_digest(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve team/project level digest."""
    service = CollaborativeIntelligenceService(db)
    return await service.get_team_digest(user=current_user, organization_id=org_id)

@router.post("/review-room", status_code=status.HTTP_200_OK)
async def create_review_context(
    req: CreateReviewRoomRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a Knowledge Review Room for resolving conflicts."""
    service = CollaborativeIntelligenceService(db)
    return await service.create_review_context(title=req.title, conflicting_sources=req.conflicting_sources)

@router.post("/resolve-review", status_code=status.HTTP_200_OK)
async def resolve_review(
    req: ResolveReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Resolve a review room and update governance state."""
    service = CollaborativeIntelligenceService(db)
    return await service.resolve_review(room_id=req.room_id, user=current_user, resolution_notes=req.resolution_notes)

@router.post("/specialized-file", status_code=status.HTTP_200_OK)
async def handle_specialized_file(
    req: SpecializedFileRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Process specialized non-renderable file format safely."""
    service = CollaborativeIntelligenceService(db)
    return await service.handle_specialized_file(filename=req.filename, mime_type=req.mime_type)
