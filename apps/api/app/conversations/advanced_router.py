from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc, update, delete, func
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from uuid import UUID, uuid4
from datetime import datetime

from ..database.session import get_session
from ..api.dependencies import get_current_user
from ..models.user import User
from ..models.conversations import Conversation, ConversationMember, DirectMessage
from ..models.advanced_messaging import MessageReaction, MessageMention, PinnedMessage, FavoriteConversation, MessageDraft
from ..websocket.manager import manager
from .messages_router import MessageResponse, SenderResponse

router = APIRouter()

class ReplyPayload(BaseModel):
    content: str = Field(..., min_length=1)
    message_type: str = "text"

class ForwardPayload(BaseModel):
    target_conversation_ids: List[UUID]

class ReactionPayload(BaseModel):
    emoji: str = Field(..., min_length=1, max_length=30)

class DraftPayload(BaseModel):
    conversation_id: UUID
    content: str

class MutePayload(BaseModel):
    is_muted: bool

class ReactionGroupResponse(BaseModel):
    emoji: str
    count: int
    user_ids: List[UUID]
    reacted_by_me: bool

class PinnedMessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    message_id: UUID
    pinned_by: UUID
    pinned_by_name: str
    pinned_at: datetime
    message: MessageResponse

async def verify_conversation_member(db: AsyncSession, conversation_id: UUID, user_id: UUID) -> ConversationMember:
    stmt = select(ConversationMember).where(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == user_id
    )
    res = await db.execute(stmt)
    mem = res.scalar_one_or_none()
    if not mem:
        conv_check_stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.is_active == True,
            Conversation.deleted_at.is_(None),
            or_(
                Conversation.participant_one == user_id,
                Conversation.participant_two == user_id
            )
        )
        cc_res = await db.execute(conv_check_stmt)
        c_found = cc_res.scalar_one_or_none()
        if not c_found:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. User is not a conversation member.")
        
        mem = ConversationMember(
            id=uuid4(),
            conversation_id=conversation_id,
            user_id=user_id,
            role="member",
            joined_at=datetime.utcnow()
        )
        db.add(mem)
        await db.commit()
        await db.refresh(mem)
    return mem

@router.post("/messages/{id}/reply", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def reply_to_message(
    id: UUID,
    payload: ReplyPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(DirectMessage).where(DirectMessage.id == id, DirectMessage.deleted == False)
    res = await db.execute(stmt)
    parent_msg = res.scalar_one_or_none()
    if not parent_msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target message to reply to not found.")

    await verify_conversation_member(db, parent_msg.conversation_id, current_user.id)

    now = datetime.utcnow()
    reply_msg = DirectMessage(
        id=uuid4(),
        conversation_id=parent_msg.conversation_id,
        sender_id=current_user.id,
        organization_id=parent_msg.organization_id,
        workspace_id=parent_msg.workspace_id,
        message_type=payload.message_type,
        content=payload.content,
        reply_to_id=parent_msg.id,
        status="sent",
        created_at=now,
        updated_at=now
    )
    db.add(reply_msg)

    # Update parent message thread counts
    parent_msg.thread_count += 1
    parent_msg.last_reply_at = now

    await db.commit()

    # Broadcast thread created/updated WebSocket event
    m_stmt = select(ConversationMember.user_id).where(ConversationMember.conversation_id == parent_msg.conversation_id)
    m_res = await db.execute(m_stmt)
    member_user_ids = [str(u) for u in m_res.scalars().all()]

    await manager.broadcast_to_users({
        "event": "thread_updated",
        "parent_message_id": str(parent_msg.id),
        "thread_count": parent_msg.thread_count,
        "last_reply_at": now.isoformat(),
        "reply_message_id": str(reply_msg.id)
    }, member_user_ids)

    return MessageResponse(
        id=reply_msg.id,
        conversation_id=reply_msg.conversation_id,
        sender_id=reply_msg.sender_id,
        sender=SenderResponse(id=current_user.id, full_name=current_user.full_name, email=current_user.email, avatar_url=current_user.avatar_url),
        message_type=reply_msg.message_type,
        content=reply_msg.content,
        reply_to_id=reply_msg.reply_to_id,
        status=reply_msg.status,
        edited=reply_msg.edited,
        deleted=reply_msg.deleted,
        created_at=reply_msg.created_at,
        updated_at=reply_msg.updated_at
    )

@router.post("/messages/{id}/forward", response_model=List[MessageResponse], status_code=status.HTTP_201_CREATED)
async def forward_message(
    id: UUID,
    payload: ForwardPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(DirectMessage, User).join(User, DirectMessage.sender_id == User.id).where(DirectMessage.id == id, DirectMessage.deleted == False)
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original message not found.")

    orig_msg, orig_sender = row

    forwarded_list = []
    now = datetime.utcnow()

    for target_conv_id in payload.target_conversation_ids:
        await verify_conversation_member(db, target_conv_id, current_user.id)

        conv_stmt = select(Conversation).where(Conversation.id == target_conv_id)
        c_res = await db.execute(conv_stmt)
        conv = c_res.scalar_one_or_none()
        if not conv:
            continue

        f_msg = DirectMessage(
            id=uuid4(),
            conversation_id=target_conv_id,
            sender_id=current_user.id,
            organization_id=conv.organization_id,
            workspace_id=conv.workspace_id,
            message_type="text",
            content=f"[Forwarded from {orig_sender.full_name}]: {orig_msg.content}",
            forwarded_from_id=orig_msg.id,
            status="sent",
            created_at=now,
            updated_at=now
        )
        db.add(f_msg)
        forwarded_list.append(f_msg)

    await db.commit()

    return [
        MessageResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            sender_id=m.sender_id,
            sender=SenderResponse(id=current_user.id, full_name=current_user.full_name, email=current_user.email, avatar_url=current_user.avatar_url),
            message_type=m.message_type,
            content=m.content,
            status=m.status,
            edited=m.edited,
            deleted=m.deleted,
            created_at=m.created_at,
            updated_at=m.updated_at
        ) for m in forwarded_list
    ]


@router.post("/messages/{id}/react", status_code=status.HTTP_200_OK)
async def add_reaction(
    id: UUID,
    payload: ReactionPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(DirectMessage).where(DirectMessage.id == id, DirectMessage.deleted == False)
    res = await db.execute(stmt)
    msg = res.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")

    await verify_conversation_member(db, msg.conversation_id, current_user.id)

    # Check if already reacted
    exist_stmt = select(MessageReaction).where(
        MessageReaction.message_id == id,
        MessageReaction.user_id == current_user.id,
        MessageReaction.emoji == payload.emoji
    )
    e_res = await db.execute(exist_stmt)
    if e_res.scalar_one_or_none():
        return {"status": "success", "message": "Already reacted"}

    reaction = MessageReaction(
        id=uuid4(),
        message_id=id,
        user_id=current_user.id,
        emoji=payload.emoji
    )
    db.add(reaction)
    await db.commit()

    # Broadcast WebSocket Event
    m_stmt = select(ConversationMember.user_id).where(ConversationMember.conversation_id == msg.conversation_id)
    m_res = await db.execute(m_stmt)
    member_user_ids = [str(u) for u in m_res.scalars().all()]

    await manager.broadcast_to_users({
        "event": "message_reaction_added",
        "message_id": str(id),
        "user_id": str(current_user.id),
        "user_name": current_user.full_name,
        "emoji": payload.emoji
    }, member_user_ids)

    return {"status": "success", "emoji": payload.emoji}

@router.delete("/messages/{id}/react", status_code=status.HTTP_200_OK)
async def remove_reaction(
    id: UUID,
    emoji: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(MessageReaction).where(
        MessageReaction.message_id == id,
        MessageReaction.user_id == current_user.id,
        MessageReaction.emoji == emoji
    )
    res = await db.execute(stmt)
    reaction = res.scalar_one_or_none()
    if not reaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reaction not found.")

    msg_stmt = select(DirectMessage).where(DirectMessage.id == id)
    m_res = await db.execute(msg_stmt)
    msg = m_res.scalar_one_or_none()

    await db.delete(reaction)
    await db.commit()

    if msg:
        m_stmt = select(ConversationMember.user_id).where(ConversationMember.conversation_id == msg.conversation_id)
        u_res = await db.execute(m_stmt)
        member_user_ids = [str(u) for u in u_res.scalars().all()]

        await manager.broadcast_to_users({
            "event": "message_reaction_removed",
            "message_id": str(id),
            "user_id": str(current_user.id),
            "emoji": emoji
        }, member_user_ids)

    return {"status": "success", "message": "Reaction removed"}

@router.post("/messages/{id}/pin", status_code=status.HTTP_200_OK)
async def pin_message(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(DirectMessage).where(DirectMessage.id == id, DirectMessage.deleted == False)
    res = await db.execute(stmt)
    msg = res.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")

    mem = await verify_conversation_member(db, msg.conversation_id, current_user.id)
    if mem.role not in ["owner", "admin", "moderator"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner, admin, or moderator can pin messages.")

    exist_stmt = select(PinnedMessage).where(
        PinnedMessage.conversation_id == msg.conversation_id,
        PinnedMessage.message_id == id
    )
    e_res = await db.execute(exist_stmt)
    if e_res.scalar_one_or_none():
        return {"status": "success", "message": "Message already pinned"}

    pinned = PinnedMessage(
        id=uuid4(),
        conversation_id=msg.conversation_id,
        message_id=id,
        pinned_by=current_user.id,
        pinned_at=datetime.utcnow()
    )
    db.add(pinned)
    await db.commit()

    # Broadcast WebSocket Event
    m_stmt = select(ConversationMember.user_id).where(ConversationMember.conversation_id == msg.conversation_id)
    u_res = await db.execute(m_stmt)
    member_user_ids = [str(u) for u in u_res.scalars().all()]

    await manager.broadcast_to_users({
        "event": "message_pinned",
        "conversation_id": str(msg.conversation_id),
        "message_id": str(id),
        "pinned_by": str(current_user.id)
    }, member_user_ids)

    return {"status": "success", "message": "Message pinned"}

@router.delete("/messages/{id}/pin", status_code=status.HTTP_200_OK)
async def unpin_message(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(PinnedMessage).where(PinnedMessage.message_id == id)
    res = await db.execute(stmt)
    pinned = res.scalar_one_or_none()
    if not pinned:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pinned message record not found.")

    mem = await verify_conversation_member(db, pinned.conversation_id, current_user.id)
    if mem.role not in ["owner", "admin", "moderator"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner, admin, or moderator can unpin messages.")

    await db.delete(pinned)
    await db.commit()

    return {"status": "success", "message": "Message unpinned"}

@router.get("/messages/{id}/thread", response_model=List[MessageResponse])
async def get_message_thread(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(DirectMessage).where(DirectMessage.id == id)
    res = await db.execute(stmt)
    parent_msg = res.scalar_one_or_none()
    if not parent_msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent message not found.")

    await verify_conversation_member(db, parent_msg.conversation_id, current_user.id)

    replies_stmt = select(DirectMessage, User).join(
        User, DirectMessage.sender_id == User.id
    ).where(
        DirectMessage.reply_to_id == id,
        DirectMessage.deleted == False
    ).order_by(DirectMessage.created_at)

    r_res = await db.execute(replies_stmt)
    rows = r_res.all()

    return [
        MessageResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            sender_id=m.sender_id,
            sender=SenderResponse(id=sender.id, full_name=sender.full_name, email=sender.email, avatar_url=sender.avatar_url),
            message_type=m.message_type,
            content=m.content,
            reply_to_id=m.reply_to_id,
            status=m.status,
            edited=m.edited,
            deleted=m.deleted,
            created_at=m.created_at,
            updated_at=m.updated_at
        ) for m, sender in rows
    ]

@router.get("/conversations/{id}/pins", response_model=List[PinnedMessageResponse])
async def get_pinned_messages(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    await verify_conversation_member(db, id, current_user.id)

    stmt = select(PinnedMessage, DirectMessage, User).join(
        DirectMessage, PinnedMessage.message_id == DirectMessage.id
    ).join(
        User, PinnedMessage.pinned_by == User.id
    ).where(
        PinnedMessage.conversation_id == id
    ).order_by(desc(PinnedMessage.pinned_at))

    res = await db.execute(stmt)
    rows = res.all()

    result = []
    for pin, msg, p_user in rows:
        # Fetch sender of message
        s_stmt = select(User).where(User.id == msg.sender_id)
        s_res = await db.execute(s_stmt)
        s_user = s_res.scalar_one_or_none()

        sender_resp = SenderResponse(id=s_user.id, full_name=s_user.full_name, email=s_user.email, avatar_url=s_user.avatar_url) if s_user else SenderResponse(id=msg.sender_id, full_name="User", email="user@example.com")

        result.append(PinnedMessageResponse(
            id=pin.id,
            conversation_id=pin.conversation_id,
            message_id=pin.message_id,
            pinned_by=pin.pinned_by,
            pinned_by_name=p_user.full_name,
            pinned_at=pin.pinned_at,
            message=MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                sender_id=msg.sender_id,
                sender=sender_resp,
                message_type=msg.message_type,
                content=msg.content,
                status=msg.status,
                edited=msg.edited,
                deleted=msg.deleted,
                created_at=msg.created_at,
                updated_at=msg.updated_at
            )
        ))

    return result


@router.post("/conversations/{id}/favorite", status_code=status.HTTP_200_OK)
async def toggle_favorite_conversation(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    await verify_conversation_member(db, id, current_user.id)

    stmt = select(FavoriteConversation).where(
        FavoriteConversation.user_id == current_user.id,
        FavoriteConversation.conversation_id == id
    )
    res = await db.execute(stmt)
    fav = res.scalar_one_or_none()

    if fav:
        await db.delete(fav)
        is_fav = False
    else:
        db.add(FavoriteConversation(id=uuid4(), user_id=current_user.id, conversation_id=id))
        is_fav = True

    await db.commit()
    return {"status": "success", "is_favorite": is_fav}

@router.patch("/conversations/{id}/mute", status_code=status.HTTP_200_OK)
async def toggle_mute_conversation(
    id: UUID,
    payload: MutePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    mem = await verify_conversation_member(db, id, current_user.id)
    mem.is_muted = payload.is_muted
    await db.commit()
    return {"status": "success", "is_muted": mem.is_muted}

@router.post("/messages/drafts", status_code=status.HTTP_200_OK)
async def save_message_draft(
    payload: DraftPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(MessageDraft).where(
        MessageDraft.user_id == current_user.id,
        MessageDraft.conversation_id == payload.conversation_id
    )
    res = await db.execute(stmt)
    draft = res.scalar_one_or_none()

    if not payload.content.strip():
        if draft:
            await db.delete(draft)
            await db.commit()
        return {"status": "success", "draft": None}

    if draft:
        draft.content = payload.content
        draft.updated_at = datetime.utcnow()
    else:
        draft = MessageDraft(
            id=uuid4(),
            user_id=current_user.id,
            conversation_id=payload.conversation_id,
            content=payload.content
        )
        db.add(draft)

    await db.commit()
    return {"status": "success", "content": draft.content}

@router.get("/messages/drafts", status_code=status.HTTP_200_OK)
async def get_message_draft(
    conversation_id: UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):

    stmt = select(MessageDraft).where(
        MessageDraft.user_id == current_user.id,
        MessageDraft.conversation_id == conversation_id
    )
    res = await db.execute(stmt)
    draft = res.scalar_one_or_none()
    return {"content": draft.content if draft else ""}
