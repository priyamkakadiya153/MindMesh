from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from ..core.database import get_db_session
from ..auth.dependencies import get_current_user
from ..models.user import User
from .service import NotificationService

router = APIRouter()

@router.get("")
@router.get("/")
async def list_notifications(
    limit: int = 50,
    offset: int = 0,
    only_unread: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    service = NotificationService(db)
    notifs = await service.list_notifications(current_user.id, limit, offset, only_unread)
    unread_count = await service.get_unread_count(current_user.id)
    
    formatted_notifs = [
        {
            "id": n.id,
            "user_id": n.user_id,
            "organization_id": getattr(n, "organization_id", None),
            "title": n.title,
            "message": n.message,
            "content": n.message,
            "type": n.type,
            "priority": n.priority,
            "is_read": n.is_read,
            "link": getattr(n, "link", None),
            "entity_type": getattr(n, "entity_type", None),
            "entity_id": getattr(n, "entity_id", None),
            "created_at": n.created_at
        }
        for n in notifs
    ]
    
    return {
        "unread_count": unread_count,
        "notifications": formatted_notifs
    }

@router.patch("/read")
@router.patch("/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    service = NotificationService(db)
    count = await service.mark_all_read(current_user.id)
    return {
        "success": True,
        "count": count
    }

@router.patch("/{id}/read")
async def mark_notification_read(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    service = NotificationService(db)
    n = await service.mark_as_read(current_user.id, id)
    return {
        "id": n.id,
        "is_read": n.is_read
    }

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    service = NotificationService(db)
    await service.delete_notification(current_user.id, id)
