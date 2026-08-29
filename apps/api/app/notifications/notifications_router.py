from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc, func
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from ..database.session import get_session
from ..api.dependencies import get_current_user
from ..models.user import User
from .models import Notification
from ..activity.models import ActivityLog

router = APIRouter()

class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    organization_id: Optional[UUID] = None
    type: str
    title: str
    message: Optional[str] = None
    content: str
    priority: Optional[str] = "normal"
    is_read: bool
    link: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    created_at: datetime

class NotificationListResponse(BaseModel):
    unread_count: int
    notifications: List[NotificationResponse]

class ActivityLogResponse(BaseModel):
    id: UUID
    organization_id: UUID
    user_id: UUID
    user_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: UUID
    details: Optional[str] = None
    created_at: datetime

@router.get("", response_model=NotificationListResponse)
@router.get("/", response_model=NotificationListResponse)
async def get_user_notifications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    unread_stmt = select(func.count(Notification.id)).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    )
    unread_res = await db.execute(unread_stmt)
    unread_count = unread_res.scalar() or 0

    stmt = select(Notification).where(
        Notification.user_id == current_user.id
    ).order_by(desc(Notification.created_at)).offset(offset).limit(limit)

    res = await db.execute(stmt)
    items = res.scalars().all()

    return NotificationListResponse(
        unread_count=unread_count,
        notifications=[
            NotificationResponse(
                id=n.id,
                user_id=n.user_id,
                organization_id=getattr(n, "organization_id", None),
                type=n.type,
                title=n.title or "Notification",
                message=getattr(n, "message", ""),
                content=getattr(n, "message", None) or getattr(n, "content", ""),
                priority=getattr(n, "priority", "normal"),
                is_read=n.is_read,
                link=getattr(n, "link", None),
                entity_type=getattr(n, "entity_type", None),
                entity_id=getattr(n, "entity_id", None),
                created_at=n.created_at
            ) for n in items
        ]
    )

@router.patch("/{id}/read", status_code=status.HTTP_200_OK)
async def mark_notification_read(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Notification).where(Notification.id == id, Notification.user_id == current_user.id)
    res = await db.execute(stmt)
    notif = res.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    notif.is_read = True
    await db.commit()
    return {"status": "success", "is_read": True}

@router.patch("/read", status_code=status.HTTP_200_OK)
@router.patch("/read-all", status_code=status.HTTP_200_OK)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = update(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).values(is_read=True)

    await db.execute(stmt)
    await db.commit()
    return {"status": "success", "message": "All notifications marked as read"}

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_notification(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Notification).where(Notification.id == id, Notification.user_id == current_user.id)
    res = await db.execute(stmt)
    notif = res.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    await db.delete(notif)
    await db.commit()
    return {"status": "success", "message": "Notification deleted"}

@router.get("/activity", response_model=List[ActivityLogResponse])
async def get_activity_feed(
    organization_id: UUID = Query(...),
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(ActivityLog, User).outerjoin(
        User, ActivityLog.user_id == User.id
    ).where(
        ActivityLog.organization_id == organization_id
    ).order_by(desc(ActivityLog.created_at)).limit(limit)

    res = await db.execute(stmt)
    rows = res.all()

    return [
        ActivityLogResponse(
            id=log.id,
            organization_id=log.organization_id,
            user_id=log.user_id,
            user_name=user.full_name if user else "System",
            action=log.event_type,
            entity_type=log.entity_type or "system",
            entity_id=log.entity_id or log.id,
            details=str(log.action_metadata) if log.action_metadata else None,
            created_at=log.created_at
        ) for log, user in rows
    ]
