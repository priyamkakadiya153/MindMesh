from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from ..database.session import get_session
from ..api.dependencies import get_current_user
from ..models.user import User
from ..models.organization_member import OrganizationMember
from ..models.conversations import Conversation, ConversationMember
from .groups_router import GroupResponse

router = APIRouter()

class ChannelCreatePayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    organization_id: UUID
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    type: str = "project_channel" # project_channel, announcement
    visibility: str = "public" # public, private, read_only, announcement

class ChannelUpdatePayload(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    visibility: Optional[str] = None

@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    payload: ChannelCreatePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    org_stmt = select(OrganizationMember).where(
        OrganizationMember.organization_id == payload.organization_id,
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.is_active == True,
        OrganizationMember.deleted_at == None
    )
    res = await db.execute(org_stmt)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not belong to this organization.")

    conv_id = uuid4()
    now = datetime.utcnow()

    channel_conv = Conversation(
        id=conv_id,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        project_id=payload.project_id,
        type=payload.type,
        name=payload.name,
        description=payload.description,
        owner_id=current_user.id,
        visibility=payload.visibility,
        created_by_user_id=current_user.id,
        created_at=now,
        updated_at=now
    )
    db.add(channel_conv)

    # Owner membership
    owner_mem = ConversationMember(
        id=uuid4(),
        conversation_id=conv_id,
        user_id=current_user.id,
        role="owner",
        joined_at=now
    )
    db.add(owner_mem)
    await db.commit()

    return GroupResponse(
        id=channel_conv.id,
        organization_id=channel_conv.organization_id,
        workspace_id=channel_conv.workspace_id,
        project_id=channel_conv.project_id,
        type=channel_conv.type,
        name=channel_conv.name,
        description=channel_conv.description,
        avatar_url=channel_conv.avatar_url,
        owner_id=channel_conv.owner_id,
        visibility=channel_conv.visibility,
        is_archived=channel_conv.is_archived,
        archived_at=channel_conv.archived_at,
        member_count=1,
        unread_count=0,
        created_at=channel_conv.created_at
    )

@router.get("", response_model=List[GroupResponse])
async def list_channels(
    organization_id: UUID,
    workspace_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Conversation).where(
        Conversation.organization_id == organization_id,
        Conversation.type.in_(["project_channel", "announcement"]),
        Conversation.is_active == True,
        Conversation.deleted_at == None
    ).order_by(desc(Conversation.created_at))

    if workspace_id:
        stmt = stmt.where(or_(Conversation.workspace_id == workspace_id, Conversation.workspace_id == None))
    if project_id:
        stmt = stmt.where(Conversation.project_id == project_id)

    res = await db.execute(stmt)
    channels = res.scalars().all()

    result = []
    for c in channels:
        result.append(GroupResponse(
            id=c.id,
            organization_id=c.organization_id,
            workspace_id=c.workspace_id,
            project_id=c.project_id,
            type=c.type,
            name=c.name or "Channel",
            description=c.description,
            avatar_url=c.avatar_url,
            owner_id=c.owner_id,
            visibility=c.visibility,
            is_archived=c.is_archived,
            archived_at=c.archived_at,
            created_at=c.created_at
        ))

    return result

@router.patch("/{id}", response_model=GroupResponse)
async def edit_channel(
    id: UUID,
    payload: ChannelUpdatePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Conversation).where(
        Conversation.id == id,
        Conversation.type.in_(["project_channel", "announcement"])
    )
    res = await db.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")

    if payload.name is not None:
        conv.name = payload.name
    if payload.description is not None:
        conv.description = payload.description
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

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_channel(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Conversation).where(Conversation.id == id)
    res = await db.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")

    conv.is_active = False
    conv.deleted_at = datetime.utcnow()
    await db.commit()

    return {"status": "success", "message": "Channel deleted successfully"}
