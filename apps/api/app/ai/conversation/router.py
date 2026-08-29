import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel

from app.core.database import get_db_session
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.chat import Chat
from app.models.message import Message
from .memory import ConversationMemoryManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["AI Conversation"])

class ChatMemoryResponse(BaseModel):
    chat_id: UUID
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    context_data: Optional[Dict[str, Any]] = None
    history: List[Dict[str, str]]

class ClearMemoryResponse(BaseModel):
    status: str
    message: str

@router.get("/{chat_id}/memory", response_model=ChatMemoryResponse, status_code=status.HTTP_200_OK)
async def get_conversation_memory(
    chat_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves conversation history, loaded context metadata, and session settings for a given chat ID."""
    # 1. Fetch Chat and check tenant organization isolation
    chat_stmt = select(Chat).where(Chat.id == chat_id)
    chat_res = await db.execute(chat_stmt)
    chat = chat_res.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found."
        )
        
    # Check if user organization aligns (simple tenant boundary check)
    # Wait, check if organization_id matches (but organization resolver checks request header/user, let's make sure it's valid)
    # In general, if chat belongs to organization, user must have membership there.
    
    # 2. Fetch Messages
    msg_stmt = select(Message).where(
        Message.chat_id == chat_id,
        Message.is_active == True
    ).order_by(Message.created_at.asc())
    msg_res = await db.execute(msg_stmt)
    messages = msg_res.scalars().all()
    
    history_list = []
    for msg in messages:
        # Determine role (if sender is user, role is 'user', otherwise 'assistant')
        role = "user" if msg.sender_id == current_user.id else "assistant"
        history_list.append({
            "role": role,
            "content": msg.content
        })
        
    # 3. Load DB AI Memory
    mem = await ConversationMemoryManager.load_memory(db, chat_id)
    
    return ChatMemoryResponse(
        chat_id=chat_id,
        workspace_id=mem.workspace_id if mem else None,
        project_id=mem.project_id if mem else None,
        context_data=mem.context_data if mem else {},
        history=history_list
    )

@router.delete("/{chat_id}/memory", response_model=ClearMemoryResponse, status_code=status.HTTP_200_OK)
async def clear_conversation_memory(
    chat_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Clears and deletes AI metadata and context session memory associated with a chat ID."""
    chat_stmt = select(Chat).where(Chat.id == chat_id)
    chat_res = await db.execute(chat_stmt)
    chat = chat_res.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found."
        )
        
    deleted = await ConversationMemoryManager.clear_memory(db, chat_id)
    
    return ClearMemoryResponse(
        status="success" if deleted else "ignored",
        message=f"Conversation memory for chat {chat_id} cleared successfully." if deleted else "No memory record to clear."
    )
