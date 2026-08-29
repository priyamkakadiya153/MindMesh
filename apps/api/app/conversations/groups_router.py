from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc, update, delete, func

from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from ..database.session import get_session
from ..api.dependencies import get_current_user
from ..models.user import User
from ..models.organization_member import OrganizationMember
from ..models.conversations import Conversation, ConversationMember, DirectMessage, UserPresence
from ..websocket.manager import manager

router = APIRouter()

class GroupCreatePayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    organization_id: UUID
    workspace_id: Optional[UUID] = None
    visibility: str = "private" # public, private, read_only, announcement
    avatar_url: Optional[str] = None
    member_user_ids: List[UUID] = []

class GroupUpdatePayload(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    visibility: Optional[str] = None

class AddMemberPayload(BaseModel):
    user_id: UUID
    role: str = "member" # member, moderator, admin

class UpdateMemberRolePayload(BaseModel):
    role: str # owner, admin, moderator, member, guest

class GroupMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    full_name: str
    email: str
    role: str
    joined_at: datetime
    avatar_url: Optional[str] = None
    status: str = "offline"

class MessageSummaryResponse(BaseModel):
    id: UUID
    sender_id: UUID
    content: str
    status: str
    created_at: datetime
    edited: bool = False
    deleted: bool = False

class GroupResponse(BaseModel):
    id: UUID
    organization_id: UUID
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    type: str = "group"
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    owner_id: Optional[UUID] = None
    visibility: str = "private"
    is_archived: bool = False
    archived_at: Optional[datetime] = None
    member_count: int = 0
    unread_count: int = 0
    created_at: datetime
    members: Optional[List[GroupMemberResponse]] = None
    last_message: Optional[MessageSummaryResponse] = None
    last_message_at: Optional[datetime] = None

async def verify_org_membership(db: AsyncSession, org_id: UUID, user_id: UUID):
    stmt = select(OrganizationMember).where(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == user_id,
        OrganizationMember.is_active == True,
        OrganizationMember.deleted_at == None
    )
    res = await db.execute(stmt)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not belong to this organization.")

@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    payload: GroupCreatePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    await verify_org_membership(db, payload.organization_id, current_user.id)

    conv_id = uuid4()
    now = datetime.utcnow()

    group_conv = Conversation(
        id=conv_id,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        type="group",
        name=payload.name,
        description=payload.description,
        avatar_url=payload.avatar_url,
        owner_id=current_user.id,
        visibility=payload.visibility,
        created_by_user_id=current_user.id,
        created_at=now,
        updated_at=now
    )
    db.add(group_conv)

    # Owner membership
    owner_mem = ConversationMember(
        id=uuid4(),
        conversation_id=conv_id,
        user_id=current_user.id,
        role="owner",
        joined_at=now
    )
    db.add(owner_mem)

    # Add initial members
    initial_member_ids = set(payload.member_user_ids) - {current_user.id}
    added_member_ids = set()
    for m_id in initial_member_ids:
        u_stmt = select(User).where(User.id == m_id, User.is_active == True)
        u_res = await db.execute(u_stmt)
        if u_res.scalar_one_or_none():
            # Ensure target member belongs to organization
            om_stmt = select(OrganizationMember).where(
                OrganizationMember.organization_id == payload.organization_id,
                OrganizationMember.user_id == m_id,
                OrganizationMember.is_active == True,
                OrganizationMember.deleted_at.is_(None)
            )
            om_res = await db.execute(om_stmt)
            if not om_res.scalar_one_or_none():
                db.add(OrganizationMember(
                    id=uuid4(),
                    organization_id=payload.organization_id,
                    user_id=m_id,
                    role="member",
                    is_active=True,
                    joined_at=now
                ))

            db.add(ConversationMember(
                id=uuid4(),
                conversation_id=conv_id,
                user_id=m_id,
                role="member",
                joined_at=now
            ))
            added_member_ids.add(m_id)

    await db.commit()

    # WebSocket Broadcast event
    try:
        all_users = [str(current_user.id)] + [str(u) for u in added_member_ids]
        await manager.broadcast_to_users({
            "event": "group_created",
            "group": {
                "id": str(group_conv.id),
                "name": group_conv.name,
                "type": group_conv.type
            }
        }, all_users)
    except Exception:
        pass

    return GroupResponse(
        id=group_conv.id,
        organization_id=group_conv.organization_id,
        workspace_id=group_conv.workspace_id,
        type=group_conv.type,
        name=group_conv.name,
        description=group_conv.description,
        avatar_url=group_conv.avatar_url,
        owner_id=group_conv.owner_id,
        visibility=group_conv.visibility,
        is_archived=group_conv.is_archived,
        archived_at=group_conv.archived_at,
        member_count=1 + len(added_member_ids),
        unread_count=0,
        created_at=group_conv.created_at
    )

@router.get("", response_model=List[GroupResponse])
async def list_groups(
    organization_id: Optional[UUID] = Query(None),
    workspace_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    # Fetch groups current user is an explicit member of OR owner/public in current org
    stmt = select(Conversation, ConversationMember).outerjoin(
        ConversationMember, and_(
            Conversation.id == ConversationMember.conversation_id,
            ConversationMember.user_id == current_user.id
        )
    ).where(
        Conversation.type.in_(["group", "project_channel", "announcement"]),
        Conversation.is_active == True,
        Conversation.deleted_at == None
    )

    if organization_id:
        stmt = stmt.where(
            or_(
                ConversationMember.user_id == current_user.id,
                and_(
                    Conversation.organization_id == organization_id,
                    or_(
                        Conversation.owner_id == current_user.id,
                        Conversation.visibility == "public"
                    )
                )
            )
        )
    else:
        stmt = stmt.where(
            or_(
                ConversationMember.user_id == current_user.id,
                Conversation.owner_id == current_user.id
            )
        )

    stmt = stmt.order_by(desc(Conversation.last_message_at), desc(Conversation.created_at))

    if workspace_id:
        stmt = stmt.where(
            or_(
                ConversationMember.user_id == current_user.id,
                Conversation.owner_id == current_user.id,
                Conversation.workspace_id == workspace_id,
                Conversation.workspace_id.is_(None)
            )
        )

    res = await db.execute(stmt)
    rows = res.all()

    result_list = []
    for conv, member in rows:
        # Count members
        count_stmt = select(func.count(ConversationMember.id)).where(ConversationMember.conversation_id == conv.id)
        c_res = await db.execute(count_stmt)
        m_count = c_res.scalar() or 0

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

        result_list.append(GroupResponse(
            id=conv.id,
            organization_id=conv.organization_id,
            workspace_id=conv.workspace_id,
            project_id=conv.project_id,
            type=conv.type,
            name=conv.name or "Group",
            description=conv.description,
            avatar_url=conv.avatar_url,
            owner_id=conv.owner_id,
            visibility=conv.visibility,
            is_archived=conv.is_archived,
            archived_at=conv.archived_at,
            member_count=m_count,
            unread_count=member.unread_count if member else 0,
            created_at=conv.created_at,
            last_message=last_msg_resp,
            last_message_at=conv.last_message_at
        ))

    return result_list

@router.get("/{id}", response_model=GroupResponse)
async def get_group_details(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Conversation).where(
        Conversation.id == id,
        Conversation.is_active == True,
        Conversation.deleted_at == None
    )
    res = await db.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group or channel not found.")

    # Check access permission
    mem_stmt = select(ConversationMember).where(
        ConversationMember.conversation_id == id,
        ConversationMember.user_id == current_user.id
    )
    m_res = await db.execute(mem_stmt)
    user_mem = m_res.scalar_one_or_none()
    if not user_mem and conv.visibility != "public":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to private group.")

    # Fetch all group members
    all_members_stmt = select(ConversationMember, User).join(
        User, ConversationMember.user_id == User.id
    ).where(ConversationMember.conversation_id == id)
    all_res = await db.execute(all_members_stmt)

    members_list = []
    for cm, u in all_res.all():
        p_info = manager.get_presence(str(u.id))
        members_list.append(GroupMemberResponse(
            id=cm.id,
            user_id=u.id,
            full_name=u.full_name,
            email=u.email,
            role=cm.role,
            joined_at=cm.joined_at,
            avatar_url=getattr(u, 'avatar_url', None),
            status=p_info.get("status", "offline")
        ))

    return GroupResponse(
        id=conv.id,
        organization_id=conv.organization_id,
        workspace_id=conv.workspace_id,
        project_id=conv.project_id,
        type=conv.type,
        name=conv.name or "Group",
        description=conv.description,
        avatar_url=conv.avatar_url,
        owner_id=conv.owner_id,
        visibility=conv.visibility,
        is_archived=conv.is_archived,
        archived_at=conv.archived_at,
        member_count=len(members_list),
        unread_count=user_mem.unread_count if user_mem else 0,
        created_at=conv.created_at,
        members=members_list
    )

@router.patch("/{id}", response_model=GroupResponse)
async def update_group(
    id: UUID,
    payload: GroupUpdatePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Conversation, ConversationMember).join(
        ConversationMember, Conversation.id == ConversationMember.conversation_id
    ).where(
        Conversation.id == id,
        ConversationMember.user_id == current_user.id
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found or unauthorized.")

    conv, member = row
    if member.role not in ["owner", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only group owner or admin can update group settings.")

    if payload.name is not None:
        conv.name = payload.name
    if payload.description is not None:
        conv.description = payload.description
    if payload.avatar_url is not None:
        conv.avatar_url = payload.avatar_url
    if payload.visibility is not None:
        conv.visibility = payload.visibility

    conv.updated_at = datetime.utcnow()
    await db.commit()

    return GroupResponse(
        id=conv.id,
        organization_id=conv.organization_id,
        workspace_id=conv.workspace_id,
        project_id=conv.project_id,
        type=conv.type,
        name=conv.name,
        description=conv.description,
        avatar_url=conv.avatar_url,
        owner_id=conv.owner_id,
        visibility=conv.visibility,
        is_archived=conv.is_archived,
        archived_at=conv.archived_at,
        created_at=conv.created_at
    )

@router.post("/{id}/members", response_model=GroupMemberResponse)
async def add_group_member(
    id: UUID,
    payload: AddMemberPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Conversation, ConversationMember).join(
        ConversationMember, Conversation.id == ConversationMember.conversation_id
    ).where(
        Conversation.id == id,
        ConversationMember.user_id == current_user.id
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")

    conv, curr_mem = row
    if curr_mem.role not in ["owner", "admin", "moderator"] and conv.visibility != "public":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to add members to this group.")

    # Check if target user is already a member
    exist_stmt = select(ConversationMember).where(
        ConversationMember.conversation_id == id,
        ConversationMember.user_id == payload.user_id
    )
    e_res = await db.execute(exist_stmt)
    if e_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this group.")

    # Fetch target user
    u_stmt = select(User).where(User.id == payload.user_id)
    u_res = await db.execute(u_stmt)
    target_user = u_res.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found.")

    # Ensure target member belongs to organization
    om_stmt = select(OrganizationMember).where(
        OrganizationMember.organization_id == conv.organization_id,
        OrganizationMember.user_id == payload.user_id,
        OrganizationMember.is_active == True,
        OrganizationMember.deleted_at.is_(None)
    )
    om_res = await db.execute(om_stmt)
    if not om_res.scalar_one_or_none():
        db.add(OrganizationMember(
            id=uuid4(),
            organization_id=conv.organization_id,
            user_id=payload.user_id,
            role="member",
            is_active=True,
            joined_at=datetime.utcnow()
        ))

    new_mem = ConversationMember(
        id=uuid4(),
        conversation_id=id,
        user_id=payload.user_id,
        role=payload.role,
        joined_at=datetime.utcnow()
    )
    db.add(new_mem)
    await db.commit()

    # Broadcast WebSocket Event to all group members including newly added member
    try:
        m_stmt = select(ConversationMember.user_id).where(ConversationMember.conversation_id == id)
        m_res = await db.execute(m_stmt)
        all_member_user_ids = [str(u) for u in m_res.scalars().all()]
        await manager.broadcast_to_users({
            "event": "group_member_added",
            "conversation_id": str(id),
            "user_id": str(payload.user_id),
            "added_by_id": str(current_user.id)
        }, all_member_user_ids)
    except Exception:
        pass

    return GroupMemberResponse(
        id=new_mem.id,
        user_id=target_user.id,
        full_name=target_user.full_name,
        email=target_user.email,
        role=new_mem.role,
        joined_at=new_mem.joined_at,
        avatar_url=getattr(target_user, 'avatar_url', None)
    )

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_group(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Conversation).where(
        Conversation.id == id,
        Conversation.type.in_(["group", "project_channel", "announcement"]),
        Conversation.is_active == True,
        Conversation.deleted_at.is_(None)
    )
    res = await db.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")

    # Check owner authorization
    owner_stmt = select(ConversationMember).where(
        ConversationMember.conversation_id == id,
        ConversationMember.user_id == current_user.id
    )
    om_res = await db.execute(owner_stmt)
    curr_mem = om_res.scalar_one_or_none()

    is_owner = (conv.owner_id == current_user.id) or (curr_mem and curr_mem.role == "owner")
    if not is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the group owner can permanently delete the group.")

    # Fetch all members for WS event before deletion
    m_stmt = select(ConversationMember.user_id).where(ConversationMember.conversation_id == id)
    m_res = await db.execute(m_stmt)
    all_member_user_ids = [str(u) for u in m_res.scalars().all()]

    # Delete messages
    del_msg_stmt = delete(DirectMessage).where(DirectMessage.conversation_id == id)
    await db.execute(del_msg_stmt)

    # Delete members
    del_mem_stmt = delete(ConversationMember).where(ConversationMember.conversation_id == id)
    await db.execute(del_mem_stmt)

    # Delete conversation
    await db.delete(conv)
    await db.commit()

    # Broadcast WebSocket Event to all former members
    try:
        await manager.broadcast_to_users({
            "event": "group_deleted",
            "conversation_id": str(id),
            "group_id": str(id),
            "deleted_by_id": str(current_user.id)
        }, all_member_user_ids)
    except Exception:
        pass

    return {"status": "success", "message": f"Group '{conv.name}' permanently deleted."}

@router.delete("/{id}/members/{user_id}", status_code=status.HTTP_200_OK)
async def remove_group_member(
    id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    conv_stmt = select(Conversation).where(Conversation.id == id)
    conv_res = await db.execute(conv_stmt)
    conv = conv_res.scalar_one_or_none()

    curr_mem_stmt = select(ConversationMember).where(
        ConversationMember.conversation_id == id,
        ConversationMember.user_id == current_user.id
    )
    c_res = await db.execute(curr_mem_stmt)
    curr_mem = c_res.scalar_one_or_none()
    if not curr_mem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group membership not found.")

    # Allowing self to leave group, or owner/admin to remove member
    if current_user.id != user_id and curr_mem.role not in ["owner", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner or admin can remove other members.")

    target_mem_stmt = select(ConversationMember).where(
        ConversationMember.conversation_id == id,
        ConversationMember.user_id == user_id
    )
    t_res = await db.execute(target_mem_stmt)
    target_mem = t_res.scalar_one_or_none()
    if not target_mem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target member not found in group.")

    # Fetch all member IDs before removal
    m_stmt = select(ConversationMember.user_id).where(ConversationMember.conversation_id == id)
    m_res = await db.execute(m_stmt)
    all_member_user_ids = [str(u) for u in m_res.scalars().all()]
    if str(user_id) not in all_member_user_ids:
        all_member_user_ids.append(str(user_id))

    # If owner is leaving, transfer ownership to oldest active member, or delete if no members remain
    if target_mem.role == "owner" or (conv and conv.owner_id == user_id):
        rem_stmt = select(ConversationMember).where(
            ConversationMember.conversation_id == id,
            ConversationMember.user_id != user_id
        ).order_by(ConversationMember.joined_at.asc())
        rem_res = await db.execute(rem_stmt)
        remaining = rem_res.scalars().all()

        if remaining:
            new_owner = remaining[0]
            new_owner.role = "owner"
            if conv:
                conv.owner_id = new_owner.user_id
        else:
            # Last member leaving: delete group cleanly
            del_msg_stmt = delete(DirectMessage).where(DirectMessage.conversation_id == id)
            await db.execute(del_msg_stmt)
            await db.delete(target_mem)
            if conv:
                await db.delete(conv)
            await db.commit()
            return {"status": "success", "message": "Last member left. Group deleted."}

    await db.delete(target_mem)
    await db.commit()

    # Broadcast WebSocket Event
    try:
        await manager.broadcast_to_users({
            "event": "group_member_removed",
            "conversation_id": str(id),
            "user_id": str(user_id),
            "removed_by_id": str(current_user.id)
        }, all_member_user_ids)
    except Exception:
        pass

    return {"status": "success", "message": "Member removed from group"}

@router.patch("/{id}/members/{user_id}/role", status_code=status.HTTP_200_OK)
async def update_member_role(
    id: UUID,
    user_id: UUID,
    payload: UpdateMemberRolePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    curr_mem_stmt = select(ConversationMember).where(
        ConversationMember.conversation_id == id,
        ConversationMember.user_id == current_user.id
    )
    c_res = await db.execute(curr_mem_stmt)
    curr_mem = c_res.scalar_one_or_none()
    if not curr_mem or curr_mem.role not in ["owner", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only group owner or admin can update member roles.")

    target_mem_stmt = select(ConversationMember).where(
        ConversationMember.conversation_id == id,
        ConversationMember.user_id == user_id
    )
    t_res = await db.execute(target_mem_stmt)
    target_mem = t_res.scalar_one_or_none()
    if not target_mem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target member not found in group.")

    target_mem.role = payload.role
    await db.commit()

    return {"status": "success", "message": f"Member role updated to {payload.role}"}

@router.post("/{id}/archive", status_code=status.HTTP_200_OK)
async def toggle_archive_group(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Conversation, ConversationMember).join(
        ConversationMember, Conversation.id == ConversationMember.conversation_id
    ).where(
        Conversation.id == id,
        ConversationMember.user_id == current_user.id
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")

    conv, member = row
    if member.role not in ["owner", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner or admin can archive/unarchive group.")

    conv.is_archived = not conv.is_archived
    conv.archived_at = datetime.utcnow() if conv.is_archived else None
    await db.commit()

    return {"status": "success", "is_archived": conv.is_archived}
