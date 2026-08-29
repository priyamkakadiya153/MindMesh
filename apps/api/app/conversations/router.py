from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc, func, update
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from ..database.session import get_session
from ..api.dependencies import get_current_user
from ..models.user import User
from ..models.organization_member import OrganizationMember
from ..models.conversations import Conversation, ConversationMember, DirectMessage, MessageRead, UserPresence
from ..websocket.manager import manager

router = APIRouter()

class PrivateConversationCreate(BaseModel):
    target_user_id: UUID
    organization_id: UUID
    workspace_id: Optional[UUID] = None

class ParticipantResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    avatar_url: Optional[str] = None
    status: str = "offline" # online, away, busy, offline
    last_seen: Optional[datetime] = None

class MessageSummaryResponse(BaseModel):
    id: UUID
    sender_id: UUID
    content: str
    status: str
    created_at: datetime
    edited: bool = False
    deleted: bool = False

class ConversationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    workspace_id: Optional[UUID] = None
    type: str = "private"
    participant: ParticipantResponse
    last_message: Optional[MessageSummaryResponse] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    created_at: datetime

def parse_last_seen(presence_dict: dict) -> Optional[datetime]:
    val = presence_dict.get("last_seen") if presence_dict else None
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val)
        except ValueError:
            return None
    elif isinstance(val, datetime):
        return val
    return None

@router.post("/private", response_model=ConversationResponse, status_code=status.HTTP_200_OK)
async def get_or_create_private_conversation(
    payload: PrivateConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    if current_user.id == payload.target_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot start a private conversation with yourself.")

    # Validate target user and current user
    org_member_stmt = select(OrganizationMember).where(
        OrganizationMember.organization_id == payload.organization_id,
        OrganizationMember.user_id == payload.target_user_id,
        OrganizationMember.is_active == True,
        OrganizationMember.deleted_at.is_(None)
    )
    res = await db.execute(org_member_stmt)
    target_member = res.scalar_one_or_none()
    if not target_member:
        # Check if target user exists in system
        tu_stmt = select(User).where(User.id == payload.target_user_id, User.is_active == True, User.deleted_at.is_(None))
        tu_res = await db.execute(tu_stmt)
        if not tu_res.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Target user does not exist.")
        
        target_member = OrganizationMember(
            id=uuid4(),
            organization_id=payload.organization_id,
            user_id=payload.target_user_id,
            role="member",
            is_active=True,
            joined_at=datetime.utcnow()
        )
        db.add(target_member)
        await db.commit()

    current_member_stmt = select(OrganizationMember).where(
        OrganizationMember.organization_id == payload.organization_id,
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.is_active == True,
        OrganizationMember.deleted_at.is_(None)
    )
    res = await db.execute(current_member_stmt)
    curr_member = res.scalar_one_or_none()
    if not curr_member:
        curr_member = OrganizationMember(
            id=uuid4(),
            organization_id=payload.organization_id,
            user_id=current_user.id,
            role="member",
            is_active=True,
            joined_at=datetime.utcnow()
        )
        db.add(curr_member)
        await db.commit()

    # Check if a 1-on-1 private conversation already exists between these 2 users in this organization
    stmt = select(Conversation).where(
        Conversation.organization_id == payload.organization_id,
        Conversation.type == "private",
        Conversation.is_active == True,
        Conversation.deleted_at.is_(None),
        or_(
            and_(Conversation.participant_one == current_user.id, Conversation.participant_two == payload.target_user_id),
            and_(Conversation.participant_one == payload.target_user_id, Conversation.participant_two == current_user.id)
        )
    )
    res = await db.execute(stmt)
    conv = res.scalars().first()

    if not conv:
        # Fallback check via ConversationMember for legacy 1-on-1 private conversations
        cm_sub = select(ConversationMember.conversation_id).where(
            ConversationMember.user_id.in_([current_user.id, payload.target_user_id])
        ).group_by(ConversationMember.conversation_id).having(func.count(ConversationMember.user_id.distinct()) == 2)
        
        legacy_stmt = select(Conversation).where(
            Conversation.id.in_(cm_sub),
            Conversation.organization_id == payload.organization_id,
            Conversation.type == "private",
            Conversation.is_active == True,
            Conversation.deleted_at.is_(None)
        )
        res = await db.execute(legacy_stmt)
        conv = res.scalars().first()
        if conv:
            conv.participant_one = current_user.id
            conv.participant_two = payload.target_user_id
            await db.commit()

    if not conv:
        # Create new private conversation
        conv_id = uuid4()
        conv = Conversation(
            id=conv_id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            type="private",
            participant_one=current_user.id,
            participant_two=payload.target_user_id,
            created_by_user_id=current_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(conv)

        # Add member entries for both users
        m1 = ConversationMember(
            id=uuid4(),
            conversation_id=conv_id,
            user_id=current_user.id,
            role="member",
            joined_at=datetime.utcnow()
        )
        m2 = ConversationMember(
            id=uuid4(),
            conversation_id=conv_id,
            user_id=payload.target_user_id,
            role="member",
            joined_at=datetime.utcnow()
        )
        db.add_all([m1, m2])
        await db.commit()
        await db.refresh(conv)

        # Broadcast WebSocket event to both participants
        await manager.broadcast_to_users({
            "event": "conversation_created",
            "conversation_id": str(conv.id),
            "organization_id": str(conv.organization_id),
            "participant_one": str(current_user.id),
            "participant_two": str(payload.target_user_id)
        }, [str(current_user.id), str(payload.target_user_id)])
    else:
        # Ensure ConversationMember records exist for BOTH users
        m_stmt = select(ConversationMember.user_id).where(ConversationMember.conversation_id == conv.id)
        m_res = await db.execute(m_stmt)
        existing_m_ids = set(m_res.scalars().all())

        new_memberships = []
        if current_user.id not in existing_m_ids:
            new_memberships.append(ConversationMember(
                id=uuid4(), conversation_id=conv.id, user_id=current_user.id, role="member", joined_at=datetime.utcnow()
            ))
        if payload.target_user_id not in existing_m_ids:
            new_memberships.append(ConversationMember(
                id=uuid4(), conversation_id=conv.id, user_id=payload.target_user_id, role="member", joined_at=datetime.utcnow()
            ))
        if new_memberships:
            db.add_all(new_memberships)
            await db.commit()

    # Fetch target user info & presence
    target_user_stmt = select(User).where(User.id == payload.target_user_id)
    res = await db.execute(target_user_stmt)
    target_user = res.scalar_one_or_none()

    presence_info = manager.get_presence(str(payload.target_user_id))

    # Fetch unread count for current user
    mem_stmt = select(ConversationMember).where(
        ConversationMember.conversation_id == conv.id,
        ConversationMember.user_id == current_user.id
    )
    res = await db.execute(mem_stmt)
    member_entry = res.scalar_one_or_none()
    unread = member_entry.unread_count if member_entry else 0

    # Fetch last message if exists
    last_msg_resp = None
    if conv.last_message_id:
        msg_stmt = select(DirectMessage).where(DirectMessage.id == conv.last_message_id)
        msg_res = await db.execute(msg_stmt)
        last_msg = msg_res.scalar_one_or_none()
        if last_msg:
            last_msg_resp = MessageSummaryResponse(
                id=last_msg.id,
                sender_id=last_msg.sender_id,
                content=last_msg.content if not last_msg.deleted else "This message was deleted",
                status=last_msg.status,
                created_at=last_msg.created_at,
                edited=last_msg.edited,
                deleted=last_msg.deleted
            )

    return ConversationResponse(
        id=conv.id,
        organization_id=conv.organization_id,
        workspace_id=conv.workspace_id,
        type=conv.type,
        participant=ParticipantResponse(
            id=target_user.id,
            full_name=target_user.full_name or target_user.email,
            email=target_user.email,
            avatar_url=getattr(target_user, 'avatar_url', None),
            status=presence_info.get("status", "offline"),
            last_seen=parse_last_seen(presence_info)
        ),
        last_message=last_msg_resp,
        last_message_at=conv.last_message_at,
        unread_count=unread,
        created_at=conv.created_at
    )

@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    organization_id: UUID,
    workspace_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    # Fetch member entries for current user (including all private DMs across organizations)
    stmt = select(Conversation, ConversationMember).join(
        ConversationMember, Conversation.id == ConversationMember.conversation_id
    ).where(
        ConversationMember.user_id == current_user.id,
        Conversation.is_active == True,
        Conversation.deleted_at.is_(None),
        or_(
            Conversation.type == "private",
            Conversation.organization_id == organization_id
        )
    ).order_by(desc(Conversation.last_message_at), desc(Conversation.created_at))

    if workspace_id:
        stmt = stmt.where(
            or_(
                Conversation.type == "private",
                ConversationMember.user_id == current_user.id,
                Conversation.workspace_id == workspace_id,
                Conversation.workspace_id.is_(None)
            )
        )

    res = await db.execute(stmt)
    rows = res.all()

    response_list = []
    seen_private_targets = set()

    for conv, member in rows:
        # Determine target participant ID
        target_user_id = conv.participant_two if conv.participant_one == current_user.id else conv.participant_one
        if not target_user_id and conv.type == "private":
            other_mem_stmt = select(ConversationMember.user_id).where(
                ConversationMember.conversation_id == conv.id,
                ConversationMember.user_id != current_user.id
            )
            om_res = await db.execute(other_mem_stmt)
            target_user_id = om_res.scalars().first()
            if target_user_id:
                conv.participant_one = current_user.id
                conv.participant_two = target_user_id
                await db.commit()

        if conv.type == "private":
            if not target_user_id:
                continue
            if target_user_id in seen_private_targets:
                continue
            seen_private_targets.add(target_user_id)

        target_user = None
        presence_info = {}
        if target_user_id:
            target_user_stmt = select(User).where(User.id == target_user_id)
            t_res = await db.execute(target_user_stmt)
            target_user = t_res.scalar_one_or_none()
            if target_user:
                presence_info = manager.get_presence(str(target_user_id))

        if conv.type == "private" and not target_user:
            continue

        last_msg_resp = None
        if conv.last_message_id:
            msg_stmt = select(DirectMessage).where(DirectMessage.id == conv.last_message_id)
            msg_res = await db.execute(msg_stmt)
            last_msg = msg_res.scalar_one_or_none()
            if last_msg:
                last_msg_resp = MessageSummaryResponse(
                    id=last_msg.id,
                    sender_id=last_msg.sender_id,
                    content=last_msg.content if not last_msg.deleted else "This message was deleted",
                    status=last_msg.status,
                    created_at=last_msg.created_at,
                    edited=last_msg.edited,
                    deleted=last_msg.deleted
                )

        response_list.append(ConversationResponse(
            id=conv.id,
            organization_id=conv.organization_id,
            workspace_id=conv.workspace_id,
            type=conv.type,
            participant=ParticipantResponse(
                id=target_user.id if target_user else current_user.id,
                full_name=(target_user.full_name if target_user else current_user.full_name) or (target_user.email if target_user else current_user.email),
                email=target_user.email if target_user else current_user.email,
                avatar_url=getattr(target_user, 'avatar_url', None) if target_user else None,
                status=presence_info.get("status", "offline"),
                last_seen=parse_last_seen(presence_info)
            ),
            last_message=last_msg_resp,
            last_message_at=conv.last_message_at,
            unread_count=member.unread_count,
            created_at=conv.created_at
        ))

    return response_list

@router.get("/{id}", response_model=ConversationResponse)
async def get_conversation_details(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    mem_stmt = select(Conversation, ConversationMember).join(
        ConversationMember, Conversation.id == ConversationMember.conversation_id
    ).where(
        Conversation.id == id,
        ConversationMember.user_id == current_user.id,
        Conversation.is_active == True,
        Conversation.deleted_at.is_(None)
    )
    res = await db.execute(mem_stmt)
    row = res.first()
    
    if not row:
        # Fallback check for private conversation participants
        conv_stmt = select(Conversation).where(
            Conversation.id == id,
            Conversation.is_active == True,
            Conversation.deleted_at.is_(None),
            or_(
                Conversation.participant_one == current_user.id,
                Conversation.participant_two == current_user.id
            )
        )
        c_res = await db.execute(conv_stmt)
        conv = c_res.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found or unauthorized.")
        
        member = ConversationMember(
            id=uuid4(),
            conversation_id=conv.id,
            user_id=current_user.id,
            role="member",
            joined_at=datetime.utcnow()
        )
        db.add(member)
        await db.commit()
        await db.refresh(member)
    else:
        conv, member = row
    target_user_id = conv.participant_two if conv.participant_one == current_user.id else conv.participant_one

    target_user_stmt = select(User).where(User.id == target_user_id)
    t_res = await db.execute(target_user_stmt)
    target_user = t_res.scalar_one_or_none()

    presence_info = manager.get_presence(str(target_user_id)) if target_user_id else {}

    last_msg_resp = None
    if conv.last_message_id:
        msg_stmt = select(DirectMessage).where(DirectMessage.id == conv.last_message_id)
        msg_res = await db.execute(msg_stmt)
        last_msg = msg_res.scalar_one_or_none()
        if last_msg:
            last_msg_resp = MessageSummaryResponse(
                id=last_msg.id,
                sender_id=last_msg.sender_id,
                content=last_msg.content if not last_msg.deleted else "This message was deleted",
                status=last_msg.status,
                created_at=last_msg.created_at,
                edited=last_msg.edited,
                deleted=last_msg.deleted
            )

    return ConversationResponse(
        id=conv.id,
        organization_id=conv.organization_id,
        workspace_id=conv.workspace_id,
        type=conv.type,
        participant=ParticipantResponse(
            id=target_user.id if target_user else current_user.id,
            full_name=(target_user.full_name if target_user else current_user.full_name) or (target_user.email if target_user else current_user.email),
            email=target_user.email if target_user else current_user.email,
            avatar_url=getattr(target_user, 'avatar_url', None) if target_user else None,
            status=presence_info.get("status", "offline"),
            last_seen=parse_last_seen(presence_info)
        ),
        last_message=last_msg_resp,
        last_message_at=conv.last_message_at,
        unread_count=member.unread_count,
        created_at=conv.created_at
    )

@router.post("/{id}/read", status_code=status.HTTP_200_OK)
async def mark_conversation_as_read(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    mem_stmt = select(ConversationMember).where(
        ConversationMember.conversation_id == id,
        ConversationMember.user_id == current_user.id
    )
    res = await db.execute(mem_stmt)
    mem = res.scalar_one_or_none()

    if not mem:
        conv_stmt = select(Conversation).where(
            Conversation.id == id,
            Conversation.is_active == True,
            Conversation.deleted_at.is_(None),
            or_(
                Conversation.participant_one == current_user.id,
                Conversation.participant_two == current_user.id
            )
        )
        c_res = await db.execute(conv_stmt)
        conv = c_res.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found or unauthorized.")
        
        mem = ConversationMember(
            id=uuid4(),
            conversation_id=id,
            user_id=current_user.id,
            role="member",
            joined_at=datetime.utcnow()
        )
        db.add(mem)
        await db.commit()

    now = datetime.utcnow()
    mem.unread_count = 0
    mem.last_read_at = now

    msg_stmt = select(DirectMessage).where(
        DirectMessage.conversation_id == id,
        DirectMessage.sender_id != current_user.id,
        DirectMessage.status != "read"
    )
    m_res = await db.execute(msg_stmt)
    unread_msgs = m_res.scalars().all()

    senders_to_notify = set()
    for m in unread_msgs:
        m.status = "read"
        m.updated_at = now
        senders_to_notify.add(str(m.sender_id))

    await db.commit()

    if senders_to_notify:
        await manager.broadcast_to_users({
            "event": "messages_read",
            "conversation_id": str(id),
            "reader_id": str(current_user.id)
        }, list(senders_to_notify))

    return {"status": "success", "read_count": len(unread_msgs)}
