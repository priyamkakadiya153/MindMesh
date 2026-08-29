import logging
from uuid import UUID
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db_session
from app.api.dependencies import get_current_user
from app.authorization.organization_resolver import resolve_organization_id
from app.models.user import User
from .models import ConversationMemory, ConversationSummary
from .summarizer import SummarizationEngine
from .manager import MemoryManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Conversation Memory & AI Summarization"])

# ---------------- PYDANTIC SCHEMAS ----------------

class MemoryResponse(BaseModel):
    id: UUID
    conversation_id: Optional[UUID] = None
    workspace_id: UUID
    organization_id: UUID
    memory_type: str
    importance: int
    content: str
    is_pinned: bool
    expiration_status: str

class SummaryResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    workspace_id: UUID
    organization_id: UUID
    summary: str
    message_range_start: int
    message_range_end: int
    key_decisions: Optional[Dict[str, Any]] = None
    action_items: Optional[Dict[str, Any]] = None
    topics: Optional[Dict[str, Any]] = None

class SummarizeRequest(BaseModel):
    conversation_id: UUID
    workspace_id: UUID
    provider: Optional[str] = "gemini"
    model: Optional[str] = "gemini-2.5-flash"

class UpdateMemoryRequest(BaseModel):
    is_pinned: Optional[bool] = None
    importance: Optional[int] = Field(None, ge=1, le=5)
    content: Optional[str] = None

# ---------------- ENDPOINTS ----------------

@router.get("/chat/memory", response_model=List[MemoryResponse], status_code=status.HTTP_200_OK)
async def get_memories_endpoint(
    workspace_id: UUID = Query(...),
    conversation_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Fetches long-term workspace and conversation memories."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id

    stmt = select(ConversationMemory).where(
        ConversationMemory.workspace_id == workspace_id,
        ConversationMemory.organization_id == org_uuid,
        ConversationMemory.deleted_at.is_(None)
    )
    if conversation_id:
        stmt = stmt.where(ConversationMemory.conversation_id == conversation_id)

    stmt = stmt.order_by(desc(ConversationMemory.is_pinned), desc(ConversationMemory.importance), desc(ConversationMemory.created_at))
    memories = (await db.execute(stmt)).scalars().all()

    return [
        MemoryResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            workspace_id=m.workspace_id,
            organization_id=m.organization_id,
            memory_type=m.memory_type,
            importance=m.importance,
            content=m.content,
            is_pinned=m.is_pinned,
            expiration_status=m.expiration_status
        )
        for m in memories
    ]

@router.get("/chat/summaries", response_model=List[SummaryResponse], status_code=status.HTTP_200_OK)
async def get_summaries_endpoint(
    conversation_id: UUID = Query(...),
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Fetches automatic conversation summaries and extracted key decisions."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id

    stmt = select(ConversationSummary).where(
        ConversationSummary.conversation_id == conversation_id,
        ConversationSummary.organization_id == org_uuid,
        ConversationSummary.deleted_at.is_(None)
    ).order_by(desc(ConversationSummary.created_at))

    summaries = (await db.execute(stmt)).scalars().all()

    return [
        SummaryResponse(
            id=s.id,
            conversation_id=s.conversation_id,
            workspace_id=s.workspace_id,
            organization_id=s.organization_id,
            summary=s.summary,
            message_range_start=s.message_range_start,
            message_range_end=s.message_range_end,
            key_decisions=s.key_decisions,
            action_items=s.action_items,
            topics=s.topics
        )
        for s in summaries
    ]

@router.post("/chat/summarize", response_model=SummaryResponse, status_code=status.HTTP_200_OK)
async def trigger_summarize_endpoint(
    request: SummarizeRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Triggers AI conversation summarization compressing history into key decisions."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id

    try:
        summary_record = await SummarizationEngine.generate_summary(
            db=db,
            conversation_id=request.conversation_id,
            organization_id=org_uuid,
            workspace_id=request.workspace_id,
            provider=request.provider or "gemini",
            model=request.model or "gemini-2.5-flash"
        )
        return SummaryResponse(
            id=summary_record.id,
            conversation_id=summary_record.conversation_id,
            workspace_id=summary_record.workspace_id,
            organization_id=summary_record.organization_id,
            summary=summary_record.summary,
            message_range_start=summary_record.message_range_start,
            message_range_end=summary_record.message_range_end,
            key_decisions=summary_record.key_decisions,
            action_items=summary_record.action_items,
            topics=summary_record.topics
        )
    except Exception as err:
        logger.error(f"Failed to generate summary: {err}")
        raise HTTPException(status_code=500, detail=str(err))

@router.patch("/chat/memory/{memory_id}", response_model=MemoryResponse, status_code=status.HTTP_200_OK)
async def update_memory_endpoint(
    memory_id: UUID,
    request: UpdateMemoryRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Updates memory item properties (pin/unpin status, content, importance)."""
    stmt = select(ConversationMemory).where(ConversationMemory.id == memory_id)
    mem = (await db.execute(stmt)).scalar_one_or_none()

    if not mem:
        raise HTTPException(status_code=404, detail="Memory item not found.")

    if request.is_pinned is not None:
        mem.is_pinned = request.is_pinned
    if request.importance is not None:
        mem.importance = request.importance
    if request.content is not None:
        mem.content = request.content

    await db.commit()
    await db.refresh(mem)

    return MemoryResponse(
        id=mem.id,
        conversation_id=mem.conversation_id,
        workspace_id=mem.workspace_id,
        organization_id=mem.organization_id,
        memory_type=mem.memory_type,
        importance=mem.importance,
        content=mem.content,
        is_pinned=mem.is_pinned,
        expiration_status=mem.expiration_status
    )

@router.delete("/chat/memory/{memory_id}", status_code=status.HTTP_200_OK)
async def delete_memory_endpoint(
    memory_id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Deletes a long-term memory item."""
    success = await MemoryManager.delete_memory(db, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory item not found.")
    return {"message": "Memory deleted successfully", "id": str(memory_id)}
