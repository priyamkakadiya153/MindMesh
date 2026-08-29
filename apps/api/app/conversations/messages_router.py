from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc, asc, func
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from ..database.session import get_session
from ..api.dependencies import get_current_user
from ..models.user import User
from ..models.conversations import Conversation, ConversationMember, DirectMessage, MessageRead
from ..models.proactive_suggestion import ProactiveSuggestion
from ..websocket.manager import manager
from ..proactive.detection_engine import ProactiveDetectionEngine

router = APIRouter()

from ..models.attachments import Attachment

class MessageCreatePayload(BaseModel):
    conversation_id: UUID
    content: Optional[str] = Field("", max_length=10000)
    message_type: str = "text"
    reply_to_id: Optional[UUID] = None
    client_msg_id: Optional[str] = None
    attachment_ids: Optional[List[UUID]] = None

class MessageUpdatePayload(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)

class SenderResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    avatar_url: Optional[str] = None

class AttachmentResponse(BaseModel):
    id: UUID
    original_filename: str
    storage_filename: str
    mime_type: str
    file_size: int
    preview_url: str
    download_url: str

class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    sender: SenderResponse
    message_type: str = "text"
    content: str
    reply_to_id: Optional[UUID] = None
    client_msg_id: Optional[str] = None
    status: str = "sent" # sending, sent, delivered, read, failed
    edited: bool = False
    deleted: bool = False
    attachments: Optional[List[AttachmentResponse]] = None
    created_at: datetime
    updated_at: datetime

async def _bg_detect_action_candidate(
    content: str,
    source_type: str,
    conversation_id: str,
    message_id: str,
    sender_id: str,
    sender_name: str,
    workspace_id: Optional[str],
    org_id: Optional[str]
):
    """Runs AUTO-08 candidate detection for all conversation members, persisting candidates and broadcasting real-time WebSocket events."""
    try:
        from ..database.session import AsyncSessionLocal
        from ..models.conversations import ConversationMember
        from ..models.user import User
        from ..models.proactive_suggestion import ProactiveSuggestion
        from ..proactive.detection_router import ProactiveSuggestionResponse
        from ..websocket.manager import manager
        from uuid import UUID
        import json

        async with AsyncSessionLocal() as db:
            # 1. Fetch all members of this conversation
            mem_stmt = select(ConversationMember, User).join(
                User, ConversationMember.user_id == User.id
            ).where(
                ConversationMember.conversation_id == UUID(conversation_id)
            )
            res = await db.execute(mem_stmt)
            rows = res.all()

            if not rows:
                return

            for cm, user_obj in rows:
                uid_str = str(user_obj.id)
                uname = user_obj.username or user_obj.full_name or user_obj.email

                # Run detection engine per user (evaluating user POV)
                candidate = ProactiveDetectionEngine.detect_candidate_action(
                    text=content,
                    source_type=source_type,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    sender_id=sender_id,
                    sender_name=sender_name,
                    current_user_id=uid_str,
                    current_user_name=uname,
                    workspace_id=workspace_id
                )

                if not candidate or candidate.confidence_level.value == "LOW" or candidate.intent.value in ("NO_ACTION", "INFORMATION_ONLY", "GENERAL_CONVERSATION", "COMPLETION_SIGNAL"):
                    continue

                # Deduplication check per user
                dup_stmt = select(ProactiveSuggestion).where(
                    ProactiveSuggestion.user_id == user_obj.id,
                    ProactiveSuggestion.detected_action_hash == candidate.detected_action_hash,
                    ProactiveSuggestion.status.in_(["DETECTED", "PENDING", "PENDING_CONFIRMATION", "SHOWN", "DISMISSED", "ACCEPTED"])
                )
                dup_res = await db.execute(dup_stmt)
                existing = dup_res.scalar_one_or_none()
                if existing:
                    continue

                # Format human provenance label
                source_label = f"From: {source_type.replace('_', ' ').title()} ({sender_name})"

                sug = ProactiveSuggestion(
                    organization_id=UUID(org_id) if org_id else None,
                    workspace_id=UUID(workspace_id) if workspace_id else None,
                    user_id=user_obj.id,
                    source_type=source_type,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    detected_action_type=candidate.candidate_type or candidate.action_type.value,
                    title=candidate.subject or content,
                    description=candidate.description,
                    deadline=candidate.deadline,
                    normalized_deadline=candidate.normalized_deadline.replace(tzinfo=None) if candidate.normalized_deadline else None,
                    assignee_name=candidate.assignee_name,
                    confidence=candidate.confidence,
                    confidence_level=candidate.confidence_level.value,
                    status="DETECTED",
                    detected_action_hash=candidate.detected_action_hash,
                    source_label=source_label,
                    source_content=content
                )
                db.add(sug)
                await db.commit()
                await db.refresh(sug)

                # Emit real-time WebSocket event
                sug_resp = ProactiveSuggestionResponse(
                    id=sug.id,
                    organization_id=sug.organization_id,
                    workspace_id=sug.workspace_id,
                    source_type=sug.source_type,
                    conversation_id=sug.conversation_id,
                    message_id=sug.message_id,
                    detected_action_type=sug.detected_action_type,
                    title=sug.title,
                    description=sug.description,
                    deadline=sug.deadline,
                    normalized_deadline=sug.normalized_deadline,
                    assignee_name=sug.assignee_name,
                    confidence=sug.confidence,
                    confidence_level=sug.confidence_level,
                    status=sug.status,
                    source_label=sug.source_label,
                    source_content=sug.source_content,
                    pending_proposal=None,
                    created_at=sug.created_at
                )

                ws_event = {
                    "event": "proactive_action_detected",
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "suggestion": sug_resp.model_dump(mode="json")
                }
                await manager.send_personal_message(ws_event, uid_str)

    except Exception as err:
        import logging
        logging.getLogger(__name__).warning(f"Background candidate detection error: {err}")

@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    payload: MessageCreatePayload,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    if not (payload.content and payload.content.strip()) and not payload.attachment_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message content or file attachment required.")

    conv_stmt = select(Conversation).where(
        Conversation.id == payload.conversation_id,
        Conversation.is_active == True,
        Conversation.deleted_at == None
    )
    c_res = await db.execute(conv_stmt)
    conv = c_res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    # Verify sender is a member of the conversation
    mem_stmt = select(ConversationMember).where(
        ConversationMember.conversation_id == payload.conversation_id,
        ConversationMember.user_id == current_user.id
    )
    res = await db.execute(mem_stmt)
    sender_member = res.scalar_one_or_none()
    if not sender_member:
        if conv.type != "private":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this conversation.")

        if conv.participant_one != current_user.id and conv.participant_two != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this conversation.")

        sender_member = ConversationMember(
            id=uuid4(),
            conversation_id=payload.conversation_id,
            user_id=current_user.id,
            role="member",
            joined_at=datetime.utcnow()
        )
        db.add(sender_member)
        await db.commit()

    # Idempotency check: if client_msg_id was provided, return existing message if already saved
    if payload.client_msg_id:
        dup_stmt = select(DirectMessage).where(
            DirectMessage.conversation_id == payload.conversation_id,
            DirectMessage.sender_id == current_user.id,
            DirectMessage.client_msg_id == payload.client_msg_id,
            DirectMessage.is_active == True,
            DirectMessage.deleted_at.is_(None)
        )
        dup_res = await db.execute(dup_stmt)
        existing_msg = dup_res.scalar_one_or_none()
        if existing_msg:
            sender_resp = SenderResponse(
                id=current_user.id,
                full_name=current_user.full_name or current_user.email,
                email=current_user.email,
                avatar_url=getattr(current_user, 'avatar_url', None)
            )
            # Fetch attachments if any
            existing_atts = []
            att_stmt = select(Attachment).where(Attachment.message_id == existing_msg.id, Attachment.status == "active")
            att_res = await db.execute(att_stmt)
            for att in att_res.scalars().all():
                existing_atts.append(AttachmentResponse(
                    id=att.id,
                    original_filename=att.original_filename,
                    storage_filename=att.storage_filename,
                    mime_type=att.mime_type,
                    file_size=att.file_size,
                    preview_url=f"/api/v1/files/{att.id}/preview",
                    download_url=f"/api/v1/files/{att.id}/download"
                ))

            return MessageResponse(
                id=existing_msg.id,
                conversation_id=existing_msg.conversation_id,
                sender_id=existing_msg.sender_id,
                sender=sender_resp,
                message_type=existing_msg.message_type,
                content=existing_msg.content,
                reply_to_id=existing_msg.reply_to_id,
                client_msg_id=existing_msg.client_msg_id,
                status=existing_msg.status,
                edited=existing_msg.edited,
                deleted=existing_msg.deleted,
                attachments=existing_atts if existing_atts else None,
                created_at=existing_msg.created_at,
                updated_at=existing_msg.updated_at
            )

    msg_id = uuid4()
    now = datetime.utcnow()

    msg = DirectMessage(
        id=msg_id,
        conversation_id=payload.conversation_id,
        sender_id=current_user.id,
        organization_id=conv.organization_id,
        workspace_id=conv.workspace_id,
        message_type=payload.message_type,
        content=(payload.content or "").strip(),
        reply_to_id=payload.reply_to_id,
        client_msg_id=payload.client_msg_id,
        status="sent",
        edited=False,
        deleted=False,
        created_at=now,
        updated_at=now
    )
    db.add(msg)
    await db.flush()

    # Process attachments if provided
    attached_resp_list = []
    if payload.attachment_ids:
        att_query = select(Attachment).where(
            Attachment.id.in_(payload.attachment_ids),
            Attachment.uploaded_by == current_user.id
        )
        att_res = await db.execute(att_query)
        attachments_to_link = att_res.scalars().all()
        for att in attachments_to_link:
            att.message_id = msg_id
            att.conversation_id = payload.conversation_id
            attached_resp_list.append(AttachmentResponse(
                id=att.id,
                original_filename=att.original_filename,
                storage_filename=att.storage_filename,
                mime_type=att.mime_type,
                file_size=att.file_size,
                preview_url=f"/api/v1/files/{att.id}/preview",
                download_url=f"/api/v1/files/{att.id}/download"
            ))

    # Update conversation last_message
    conv.last_message_id = msg_id
    conv.last_message_at = now
    conv.updated_at = now

    # Increment unread count for recipient(s)
    recipient_mem_stmt = select(ConversationMember).where(
        ConversationMember.conversation_id == payload.conversation_id,
        ConversationMember.user_id != current_user.id
    )
    rec_res = await db.execute(recipient_mem_stmt)
    recipients = rec_res.scalars().all()

    recipient_ids = []
    is_any_rec_online = False
    for rec in recipients:
        rec.unread_count = (rec.unread_count or 0) + 1
        rec_id_str = str(rec.user_id)
        recipient_ids.append(rec_id_str)
        if rec_id_str in manager.user_sessions and len(manager.user_sessions[rec_id_str]) > 0:
            is_any_rec_online = True

    if is_any_rec_online:
        msg.status = "delivered"

    await db.commit()

    sender_resp = SenderResponse(
        id=current_user.id,
        full_name=current_user.full_name or current_user.email,
        email=current_user.email,
        avatar_url=getattr(current_user, 'avatar_url', None)
    )

    msg_dict = {
        "event": "new_message",
        "message": {
            "id": str(msg.id),
            "conversation_id": str(msg.conversation_id),
            "sender_id": str(msg.sender_id),
            "sender": {
                "id": str(current_user.id),
                "full_name": current_user.full_name or current_user.email,
                "email": current_user.email,
                "avatar_url": getattr(current_user, 'avatar_url', None)
            },
            "message_type": msg.message_type,
            "content": msg.content,
            "reply_to_id": str(msg.reply_to_id) if msg.reply_to_id else None,
            "client_msg_id": msg.client_msg_id,
            "status": msg.status,
            "edited": msg.edited,
            "deleted": msg.deleted,
            "attachments": [a.model_dump(mode='json') for a in attached_resp_list] if attached_resp_list else None,
            "created_at": msg.created_at.isoformat(),
            "updated_at": msg.updated_at.isoformat()
        }
    }

    # Broadcast real-time WebSocket event to all participants
    all_target_users = recipient_ids + [str(current_user.id)]
    await manager.broadcast_to_users(msg_dict, all_target_users)

    if msg.content:
        background_tasks.add_task(
            _bg_detect_action_candidate,
            msg.content,
            "DIRECT_MESSAGE",
            str(msg.conversation_id),
            str(msg.id),
            str(current_user.id),
            current_user.username or current_user.full_name or "User",
            str(conv.workspace_id) if conv.workspace_id else None,
            str(conv.organization_id) if conv.organization_id else None
        )

    return MessageResponse(
        id=msg.id,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
        sender=sender_resp,
        message_type=msg.message_type,
        content=msg.content,
        reply_to_id=msg.reply_to_id,
        client_msg_id=msg.client_msg_id,
        status=msg.status,
        edited=msg.edited,
        deleted=msg.deleted,
        attachments=attached_resp_list if attached_resp_list else None,
        created_at=msg.created_at,
        updated_at=msg.updated_at
    )

@router.get("", response_model=List[MessageResponse])
async def search_messages(
    query: str = Query(..., min_length=1),
    conversation_id: Optional[UUID] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    # Find conversations current user belongs to
    conv_mems_stmt = select(ConversationMember.conversation_id).where(ConversationMember.user_id == current_user.id)
    res = await db.execute(conv_mems_stmt)
    user_conv_ids = [row[0] for row in res.all()]

    if not user_conv_ids:
        return []

    if conversation_id:
        if conversation_id not in user_conv_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to conversation.")
        search_conv_ids = [conversation_id]
    else:
        search_conv_ids = user_conv_ids

    stmt = select(DirectMessage, User).join(
        User, DirectMessage.sender_id == User.id
    ).where(
        DirectMessage.conversation_id.in_(search_conv_ids),
        DirectMessage.content.ilike(f"%{query}%"),
        DirectMessage.deleted == False,
        DirectMessage.is_active == True,
        DirectMessage.deleted_at == None
    ).order_by(desc(DirectMessage.created_at)).offset(offset).limit(limit)

    result = await db.execute(stmt)
    messages = []
    for msg, sender_user in result.all():
        messages.append(MessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            sender_id=msg.sender_id,
            sender=SenderResponse(
                id=sender_user.id,
                full_name=sender_user.full_name or sender_user.email,
                email=sender_user.email,
                avatar_url=getattr(sender_user, 'avatar_url', None)
            ),
            message_type=msg.message_type,
            content=msg.content,
            reply_to_id=msg.reply_to_id,
            client_msg_id=msg.client_msg_id,
            status=msg.status,
            edited=msg.edited,
            deleted=msg.deleted,
            created_at=msg.created_at,
            updated_at=msg.updated_at
        ))

    return messages

@router.get("/{conversation_id}", response_model=List[MessageResponse])
async def get_messages_history(
    conversation_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    conv_stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.is_active == True,
        Conversation.deleted_at.is_(None)
    )
    c_res = await db.execute(conv_stmt)
    conv = c_res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    # Verify membership
    mem_stmt = select(ConversationMember).where(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == current_user.id
    )
    res = await db.execute(mem_stmt)
    if not res.scalar_one_or_none():
        if conv.type != "private":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to conversation.")

        if conv.participant_one != current_user.id and conv.participant_two != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to conversation.")

        new_mem = ConversationMember(
            id=uuid4(),
            conversation_id=conversation_id,
            user_id=current_user.id,
            role="member",
            joined_at=datetime.utcnow()
        )
        db.add(new_mem)
        await db.commit()

    safe_limit = int(limit) if isinstance(limit, (int, str)) and str(limit).isdigit() else 50
    safe_offset = int(offset) if isinstance(offset, (int, str)) and str(offset).isdigit() else 0

    stmt = select(DirectMessage, User).join(
        User, DirectMessage.sender_id == User.id
    ).where(
        DirectMessage.conversation_id == conversation_id,
        DirectMessage.is_active == True,
        DirectMessage.deleted_at == None
    ).order_by(asc(DirectMessage.created_at)).offset(safe_offset).limit(safe_limit)

    result = await db.execute(stmt)
    rows = result.all()

    msg_ids = [msg.id for msg, _ in rows]
    attachments_by_msg = {}
    if msg_ids:
        att_stmt = select(Attachment).where(Attachment.message_id.in_(msg_ids), Attachment.status == "active")
        att_res = await db.execute(att_stmt)
        for att in att_res.scalars().all():
            if att.message_id not in attachments_by_msg:
                attachments_by_msg[att.message_id] = []
            attachments_by_msg[att.message_id].append(AttachmentResponse(
                id=att.id,
                original_filename=att.original_filename,
                storage_filename=att.storage_filename,
                mime_type=att.mime_type,
                file_size=att.file_size,
                preview_url=f"/api/v1/files/{att.id}/preview",
                download_url=f"/api/v1/files/{att.id}/download"
            ))

    messages = []
    for msg, sender_user in rows:
        messages.append(MessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            sender_id=msg.sender_id,
            sender=SenderResponse(
                id=sender_user.id,
                full_name=sender_user.full_name or sender_user.email,
                email=sender_user.email,
                avatar_url=getattr(sender_user, 'avatar_url', None)
            ),
            message_type=msg.message_type,
            content=msg.content if not msg.deleted else "This message was deleted",
            reply_to_id=msg.reply_to_id,
            client_msg_id=msg.client_msg_id,
            status=msg.status,
            edited=msg.edited,
            deleted=msg.deleted,
            attachments=attachments_by_msg.get(msg.id, None),
            created_at=msg.created_at,
            updated_at=msg.updated_at
        ))

    return messages

@router.patch("/{id}", response_model=MessageResponse)
async def edit_message(
    id: UUID,
    payload: MessageUpdatePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(DirectMessage).where(DirectMessage.id == id)
    res = await db.execute(stmt)
    msg = res.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")

    if msg.sender_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only edit your own messages.")

    if msg.deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot edit a deleted message.")

    msg.content = payload.content
    msg.edited = True
    msg.updated_at = datetime.utcnow()
    await db.commit()

    # Notify participants of edit via WebSocket
    mem_stmt = select(ConversationMember.user_id).where(ConversationMember.conversation_id == msg.conversation_id)
    m_res = await db.execute(mem_stmt)
    member_user_ids = [str(r[0]) for r in m_res.all()]

    await manager.broadcast_to_users({
        "event": "message_edited",
        "message": {
            "id": str(msg.id),
            "conversation_id": str(msg.conversation_id),
            "content": msg.content,
            "status": msg.status,
            "edited": True,
            "created_at": msg.created_at.isoformat(),
            "updated_at": msg.updated_at.isoformat()
        }
    }, member_user_ids)

    sender_resp = SenderResponse(
        id=current_user.id,
        full_name=current_user.full_name or current_user.email,
        email=current_user.email,
        avatar_url=getattr(current_user, 'avatar_url', None)
    )

    return MessageResponse(
        id=msg.id,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
        sender=sender_resp,
        message_type=msg.message_type,
        content=msg.content,
        reply_to_id=msg.reply_to_id,
        status=msg.status,
        edited=msg.edited,
        deleted=msg.deleted,
        created_at=msg.created_at,
        updated_at=msg.updated_at
    )

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_message(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(DirectMessage).where(DirectMessage.id == id)
    res = await db.execute(stmt)
    msg = res.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")

    if msg.sender_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own messages.")

    msg.deleted = True
    msg.content = "This message was deleted"
    msg.updated_at = datetime.utcnow()
    await db.commit()

    # Notify participants of deletion via WebSocket
    mem_stmt = select(ConversationMember.user_id).where(ConversationMember.conversation_id == msg.conversation_id)
    m_res = await db.execute(mem_stmt)
    member_user_ids = [str(r[0]) for r in m_res.all()]

    await manager.broadcast_to_users({
        "event": "message_deleted",
        "message": {
            "id": str(msg.id),
            "conversation_id": str(msg.conversation_id),
            "deleted": True,
            "content": "This message was deleted",
            "updated_at": msg.updated_at.isoformat()
        }
    }, member_user_ids)

    return {"status": "success", "message": "Message soft deleted successfully"}
