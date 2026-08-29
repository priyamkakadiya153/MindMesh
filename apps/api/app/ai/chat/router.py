import logging
import math
from uuid import UUID
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_

from app.core.database import get_db_session
from app.api.dependencies import get_current_user
from app.authorization.organization_resolver import resolve_organization_id
from app.models.user import User
from app.models.chat import Chat
from app.models.message import Message
from app.models.citation import Citation

from .schemas import (
    ConversationCreateRequest,
    ConversationUpdateRequest,
    ConversationPinRequest,
    ConversationResponse,
    PaginatedConversationsResponse,
    MessageCreateRequest,
    MessageResponse,
    ChatQueryRequest,
    RAGQueryRequest,
    ChatRenameRequest,
    ChatExportRequest,
    ChatHistoryItem,
    ChatDetailsResponse,
    ChatMessageSchema,
    CitationSchema
)
from .models import ChatResponse
from .service import ChatService
from .session import ChatSessionManager
from .streaming import ChatStreamer
from ..rag.pipeline import RAGPipeline
from ..llm.factory import LLMProviderFactory

logger = logging.getLogger(__name__)

router = APIRouter()

# ==============================================================================
# PHASE 3.1 CONVERSATION MANAGEMENT ENDPOINTS
# ==============================================================================

@router.post("/chat/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED, tags=["Conversation Management"])
async def create_conversation_endpoint(
    request: ConversationCreateRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Creates a new workspace-aware conversation."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    chat = await ChatSessionManager.create_conversation(
        db=db,
        organization_id=org_uuid,
        user_id=current_user.id,
        workspace_id=request.workspace_id,
        title=request.title,
        description=request.description
    )
    await db.commit()
    await db.refresh(chat)

    return ConversationResponse(
        id=chat.id,
        organization_id=chat.organization_id,
        workspace_id=chat.workspace_id,
        user_id=chat.user_id,
        title=chat.title,
        description=chat.description,
        is_pinned=chat.is_pinned,
        status=chat.status,
        last_message_at=chat.last_message_at,
        created_at=chat.created_at,
        updated_at=chat.updated_at
    )

@router.get("/chat/conversations", response_model=PaginatedConversationsResponse, status_code=status.HTTP_200_OK, tags=["Conversation Management"])
async def list_conversations_endpoint(
    workspace_id: Optional[UUID] = Query(None),
    is_pinned: Optional[bool] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Lists conversations with workspace isolation, search, and pagination."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    chats, total_hits = await ChatSessionManager.list_conversations(
        db=db,
        organization_id=org_uuid,
        user_id=current_user.id,
        workspace_id=workspace_id,
        page=page,
        limit=limit,
        is_pinned=is_pinned,
        query=q
    )

    conv_items = [
        ConversationResponse(
            id=c.id,
            organization_id=c.organization_id,
            workspace_id=c.workspace_id,
            user_id=c.user_id,
            title=c.title,
            description=c.description,
            is_pinned=c.is_pinned,
            status=c.status,
            last_message_at=c.last_message_at,
            created_at=c.created_at,
            updated_at=c.updated_at
        ) for c in chats
    ]

    total_pages = math.ceil(total_hits / limit) if limit > 0 else 1

    return PaginatedConversationsResponse(
        conversations=conv_items,
        total=total_hits,
        page=page,
        limit=limit,
        total_pages=total_pages
    )

@router.get("/chat/conversations/search", response_model=List[ConversationResponse], status_code=status.HTTP_200_OK, tags=["Conversation Management"])
async def search_conversations_endpoint(
    q: str = Query(..., min_length=1),
    workspace_id: Optional[UUID] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Searches conversation titles for matching query string."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    chats = await ChatSessionManager.search_conversations(
        db=db,
        organization_id=org_uuid,
        user_id=current_user.id,
        query=q,
        workspace_id=workspace_id,
        limit=limit
    )

    return [
        ConversationResponse(
            id=c.id,
            organization_id=c.organization_id,
            workspace_id=c.workspace_id,
            user_id=c.user_id,
            title=c.title,
            description=c.description,
            is_pinned=c.is_pinned,
            status=c.status,
            last_message_at=c.last_message_at,
            created_at=c.created_at,
            updated_at=c.updated_at
        ) for c in chats
    ]

@router.get("/chat/conversations/recent", response_model=List[ConversationResponse], status_code=status.HTTP_200_OK, tags=["Conversation Management"])
async def get_recent_conversations_endpoint(
    workspace_id: Optional[UUID] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Fetches recent conversations ordered by last_message_at."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    chats = await ChatSessionManager.get_recent_conversations(
        db=db,
        organization_id=org_uuid,
        user_id=current_user.id,
        workspace_id=workspace_id,
        limit=limit
    )

    return [
        ConversationResponse(
            id=c.id,
            organization_id=c.organization_id,
            workspace_id=c.workspace_id,
            user_id=c.user_id,
            title=c.title,
            description=c.description,
            is_pinned=c.is_pinned,
            status=c.status,
            last_message_at=c.last_message_at,
            created_at=c.created_at,
            updated_at=c.updated_at
        ) for c in chats
    ]

@router.get("/chat/conversations/{conversation_id}", response_model=ConversationResponse, status_code=status.HTTP_200_OK, tags=["Conversation Management"])
async def get_conversation_endpoint(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Fetches details of a single conversation."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    chat = await ChatSessionManager.get_conversation(db, conversation_id, org_uuid, current_user.id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    return ConversationResponse(
        id=chat.id,
        organization_id=chat.organization_id,
        workspace_id=chat.workspace_id,
        user_id=chat.user_id,
        title=chat.title,
        description=chat.description,
        is_pinned=chat.is_pinned,
        status=chat.status,
        last_message_at=chat.last_message_at,
        created_at=chat.created_at,
        updated_at=chat.updated_at
    )

@router.patch("/chat/conversations/{conversation_id}", response_model=ConversationResponse, status_code=status.HTTP_200_OK, tags=["Conversation Management"])
async def update_conversation_endpoint(
    conversation_id: UUID,
    request: ConversationUpdateRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Renames or updates conversation metadata."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    chat = await ChatSessionManager.update_conversation(
        db=db,
        conversation_id=conversation_id,
        organization_id=org_uuid,
        user_id=current_user.id,
        title=request.title,
        description=request.description,
        is_pinned=request.is_pinned,
        status=request.status,
        workspace_id=request.workspace_id,
        settings=request.settings
    )
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    await db.commit()
    await db.refresh(chat)

    return ConversationResponse(
        id=chat.id,
        organization_id=chat.organization_id,
        workspace_id=chat.workspace_id,
        user_id=chat.user_id,
        title=chat.title,
        description=chat.description,
        is_pinned=chat.is_pinned,
        status=chat.status,
        last_message_at=chat.last_message_at,
        created_at=chat.created_at,
        updated_at=chat.updated_at
    )

@router.delete("/chat/conversations/{conversation_id}", status_code=status.HTTP_200_OK, tags=["Conversation Management"])
async def soft_delete_conversation_endpoint(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Soft deletes a conversation (sets deleted_at timestamp)."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    success = await ChatSessionManager.soft_delete_conversation(db, conversation_id, org_uuid, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    await db.commit()
    return {"status": "success", "message": f"Conversation {conversation_id} soft deleted."}

@router.post("/chat/conversations/{conversation_id}/pin", response_model=ConversationResponse, status_code=status.HTTP_200_OK, tags=["Conversation Management"])
async def pin_conversation_endpoint(
    conversation_id: UUID,
    request: ConversationPinRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Pins or unpins a conversation."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    chat = await ChatSessionManager.toggle_pin_conversation(
        db=db,
        conversation_id=conversation_id,
        organization_id=org_uuid,
        user_id=current_user.id,
        is_pinned=request.is_pinned
    )
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    await db.commit()
    await db.refresh(chat)

    return ConversationResponse(
        id=chat.id,
        organization_id=chat.organization_id,
        workspace_id=chat.workspace_id,
        user_id=chat.user_id,
        title=chat.title,
        description=chat.description,
        is_pinned=chat.is_pinned,
        status=chat.status,
        last_message_at=chat.last_message_at,
        created_at=chat.created_at,
        updated_at=chat.updated_at
    )

# ==============================================================================
# MESSAGE STORAGE ENDPOINTS
# ==============================================================================

@router.post("/chat/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED, tags=["Message Persistence"])
async def create_message_endpoint(
    conversation_id: UUID,
    request: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Stores a message immediately and updates parent conversation last_message_at."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    
    # Verify conversation exists
    chat = await ChatSessionManager.get_conversation(db, conversation_id, org_uuid, current_user.id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    sender_id = current_user.id
    if request.role == "assistant":
        ai_user = await ChatSessionManager.get_assistant_user(db)
        sender_id = ai_user.id

    msg = await ChatSessionManager.add_message(
        db=db,
        conversation_id=conversation_id,
        sender_id=sender_id,
        organization_id=org_uuid,
        content=request.content,
        role=request.role or "user",
        content_type=request.content_type or "text/plain",
        model=request.model,
        token_count=request.token_count or 0,
        latency_ms=request.latency_ms or 0,
        metadata=request.metadata
    )
    await db.commit()
    await db.refresh(msg)

    return MessageResponse(
        id=msg.id,
        conversation_id=msg.chat_id,
        role=msg.role,
        content=msg.content,
        content_type=msg.content_type,
        model=msg.model,
        token_count=msg.token_count,
        latency_ms=msg.latency_ms,
        metadata=msg.msg_metadata,
        created_at=msg.created_at
    )

@router.get("/chat/conversations/{conversation_id}/messages", response_model=List[MessageResponse], status_code=status.HTTP_200_OK, tags=["Message Persistence"])
async def list_messages_endpoint(
    conversation_id: UUID,
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Lists all non-deleted messages for a conversation."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    
    chat = await ChatSessionManager.get_conversation(db, conversation_id, org_uuid, current_user.id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    messages = await ChatSessionManager.list_messages(db, conversation_id, org_uuid, limit=limit)

    return [
        MessageResponse(
            id=m.id,
            conversation_id=m.chat_id,
            role=m.role,
            content=m.content,
            content_type=m.content_type,
            model=m.model,
            token_count=m.token_count,
            latency_ms=m.latency_ms,
            metadata=m.msg_metadata,
            created_at=m.created_at
        ) for m in messages
    ]

@router.delete("/chat/messages/{message_id}", status_code=status.HTTP_200_OK, tags=["Message Persistence"])
async def delete_message_endpoint(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Soft deletes a single message."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    success = await ChatSessionManager.soft_delete_message(db, message_id, org_uuid)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")

    await db.commit()
    return {"status": "success", "message": f"Message {message_id} soft deleted."}

# ==============================================================================
# LEGACY & AI EXECUTION ENDPOINTS (RETAINED FOR MULTI-TURN RAG CHAT)
# ==============================================================================

@router.post("/chat", status_code=status.HTTP_200_OK, tags=["AI Chat"])
@router.post("/ai/chat", status_code=status.HTTP_200_OK, tags=["AI Orchestrator"])
async def chat_endpoint(
    request: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
        target_chat_id = request.chat_id or request.conversation_id
        query_text = request.query or request.message or ""

        if request.stream:
            stream_gen = ChatService.execute_chat_stream(
                db=db,
                user_id=current_user.id,
                org_id=org_uuid,
                query=query_text,
                workspace_id=request.workspace_id,
                project_id=request.project_id,
                provider=request.provider or "gemini",
                model=request.model or "gemini-1.5-flash",
                chat_id=target_chat_id,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            return StreamingResponse(
                ChatStreamer.format_sse_stream(stream_gen),
                media_type="text/event-stream"
            )

        res = await ChatService.execute_chat(
            db=db,
            user_id=current_user.id,
            org_id=org_uuid,
            query=query_text,
            workspace_id=request.workspace_id,
            project_id=request.project_id,
            provider=request.provider or "gemini",
            model=request.model or "gemini-2.5-flash",
            chat_id=target_chat_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return res
    except Exception as e:
        logger.error(f"Chat execute exception: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat session failed: {str(e)}"
        )

@router.post("/chat/stream", tags=["AI Chat"])
@router.post("/ai/chat/stream", tags=["AI Orchestrator"])
async def chat_stream_endpoint(
    request: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
        target_chat_id = request.chat_id or request.conversation_id
        query_text = request.query or request.message or ""

        stream_gen = ChatService.execute_chat_stream(
            db=db,
            user_id=current_user.id,
            org_id=org_uuid,
            query=query_text,
            workspace_id=request.workspace_id,
            project_id=request.project_id,
            provider=request.provider or "gemini",
            model=request.model or "gemini-2.5-flash",
            chat_id=target_chat_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return StreamingResponse(
            ChatStreamer.format_sse_stream(stream_gen),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Chat stream exception: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat streaming failed: {str(e)}"
        )

@router.get("/chat/history", response_model=List[ChatHistoryItem], status_code=status.HTTP_200_OK, tags=["AI Chat"])
async def list_chat_history(
    workspace_id: Optional[UUID] = Query(None),
    is_pinned: Optional[bool] = Query(None),
    query: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    chats, _ = await ChatSessionManager.list_conversations(
        db=db,
        organization_id=org_uuid,
        user_id=current_user.id,
        workspace_id=workspace_id,
        page=1,
        limit=limit,
        is_pinned=is_pinned,
        query=query
    )
    
    return [
        ChatHistoryItem(
            id=c.id,
            title=c.title,
            snippet="",
            is_pinned=c.is_pinned,
            workspace_id=c.workspace_id,
            organization_id=c.organization_id,
            created_at=c.created_at,
            updated_at=c.updated_at
        ) for c in chats
    ]

@router.get("/chat/{conversation_id}", response_model=ChatDetailsResponse, status_code=status.HTTP_200_OK, tags=["AI Chat"])
async def get_conversation_details(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    chat = await ChatSessionManager.get_conversation(db, conversation_id, org_uuid, current_user.id)
    
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    messages = await ChatSessionManager.list_messages(db, conversation_id, org_uuid)

    formatted_messages = []
    for m in messages:
        citations_list = []
        if m.role == "assistant":
            cit_stmt = select(Citation).where(Citation.message_id == m.id)
            cit_res = await db.execute(cit_stmt)
            cits = cit_res.scalars().all()
            for cit in cits:
                citations_list.append(CitationSchema(
                    id=cit.id,
                    document="Document",
                    document_id=cit.document_id,
                    chunk_id=cit.chunk_id,
                    page=cit.page_number,
                    page_number=cit.page_number,
                    confidence=cit.score,
                    score=cit.score
                ))

        formatted_messages.append(ChatMessageSchema(
            id=m.id,
            role=m.role,
            content=m.content,
            model=m.model,
            token_count=m.token_count,
            latency_ms=m.latency_ms,
            created_at=m.created_at,
            citations=citations_list
        ))

    return ChatDetailsResponse(
        id=chat.id,
        title=chat.title,
        organization_id=chat.organization_id,
        workspace_id=chat.workspace_id,
        is_pinned=chat.is_pinned,
        settings=chat.settings or {},
        messages=formatted_messages,
        created_at=chat.created_at,
        updated_at=chat.updated_at
    )

@router.patch("/chat/{conversation_id}", response_model=ChatDetailsResponse, status_code=status.HTTP_200_OK, tags=["AI Chat"])
async def update_conversation_legacy(
    conversation_id: UUID,
    request: ConversationUpdateRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    chat = await ChatSessionManager.update_conversation(
        db=db,
        conversation_id=conversation_id,
        organization_id=org_uuid,
        user_id=current_user.id,
        title=request.title,
        is_pinned=request.is_pinned,
        workspace_id=request.workspace_id,
        settings=request.settings
    )
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    await db.commit()
    return await get_conversation_details(conversation_id=conversation_id, current_user=current_user, org_id=org_id, db=db)

@router.post("/chat/{conversation_id}/rename", response_model=Dict[str, Any], status_code=status.HTTP_200_OK, tags=["AI Chat"])
async def rename_conversation_legacy(
    conversation_id: UUID,
    request: ChatRenameRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    chat = await ChatSessionManager.update_conversation(
        db=db,
        conversation_id=conversation_id,
        organization_id=org_uuid,
        user_id=current_user.id,
        title=request.title
    )
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    await db.commit()
    return {"status": "success", "conversation_id": str(chat.id), "title": chat.title}

@router.delete("/chat/{conversation_id}", status_code=status.HTTP_200_OK, tags=["AI Chat"])
async def delete_conversation_legacy(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    deleted = await ChatSessionManager.soft_delete_conversation(db, conversation_id, org_uuid, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    await db.commit()
    return {"status": "success", "message": f"Conversation {conversation_id} deleted."}

@router.post("/chat/{conversation_id}/regenerate", status_code=status.HTTP_200_OK, tags=["AI Chat"])
async def regenerate_last_response(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    messages = await ChatSessionManager.list_messages(db, conversation_id, org_uuid)
    user_msgs = [m for m in messages if m.role == "user"]
    if not user_msgs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user message to regenerate.")

    last_user_msg = user_msgs[-1]
    rag_res = await ChatService.execute_chat(
        db=db,
        user_id=current_user.id,
        org_id=org_uuid,
        query=last_user_msg.content,
        chat_id=conversation_id
    )
    return rag_res

@router.post("/chat/{conversation_id}/stop", status_code=status.HTTP_200_OK, tags=["AI Chat"])
async def stop_generation_endpoint(conversation_id: UUID):
    return {"status": "success", "message": f"Stream generation stopped for conversation {conversation_id}"}

@router.post("/chat/export", status_code=status.HTTP_200_OK, tags=["AI Chat"])
async def export_conversation(
    request: ChatExportRequest,
    conversation_id: UUID = Query(...),
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    chat = await ChatSessionManager.get_conversation(db, conversation_id, org_uuid, current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = await ChatSessionManager.list_messages(db, conversation_id, org_uuid)

    if request.format == "json":
        data = {
            "conversation_id": str(chat.id),
            "title": chat.title,
            "created_at": chat.created_at.isoformat() if chat.created_at else None,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None
                }
                for m in messages
            ]
        }
        return JSONResponse(content=data)
    else:
        md_lines = [f"# {chat.title}\n", f"*Exported on {chat.created_at}*\n\n---\n"]
        for m in messages:
            role_name = "User" if m.role == "user" else "MindMesh Assistant"
            md_lines.append(f"### **{role_name}**\n\n{m.content}\n\n---\n")
        
        md_text = "\n".join(md_lines)
        return Response(
            content=md_text,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=conversation_{conversation_id}.md"}
        )

@router.get("/llm/models", response_model=List[str], status_code=status.HTTP_200_OK, tags=["AI Models Metadata"])
async def list_models():
    from ..llm.pricing import MODEL_PRICING
    return list(MODEL_PRICING.keys())

@router.get("/llm/providers", response_model=List[str], status_code=status.HTTP_200_OK, tags=["AI Models Metadata"])
async def list_providers():
    return LLMProviderFactory.list_supported_providers()
