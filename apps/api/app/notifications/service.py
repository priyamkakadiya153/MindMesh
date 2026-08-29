from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from .repository import NotificationRepository
from .models import Notification
from fastapi import HTTPException

class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = NotificationRepository(db)

    async def create_notification(
        self,
        user_id: UUID,
        title: str,
        message: str,
        type: str = "info",
        priority: str = "normal",
        organization_id: Optional[UUID] = None,
        link: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None
    ) -> Notification:
        return await self.repo.create(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            priority=priority,
            organization_id=organization_id,
            link=link,
            entity_type=entity_type,
            entity_id=entity_id
        )

    async def list_notifications(
        self, user_id: UUID, limit: int = 50, offset: int = 0, only_unread: bool = False
    ) -> List[Notification]:
        return await self.repo.list_for_user(user_id, limit, offset, only_unread)

    async def get_unread_count(self, user_id: UUID) -> int:
        return await self.repo.get_unread_count(user_id)

    async def mark_as_read(self, user_id: UUID, id: UUID) -> Notification:
        notif = await self.repo.mark_read(user_id, id)
        if not notif:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notif

    async def mark_read_by_entity(self, user_id: UUID, entity_type: str, entity_id: UUID) -> int:
        return await self.repo.mark_read_by_entity(user_id, entity_type, entity_id)

    async def mark_all_read(self, user_id: UUID) -> int:
        return await self.repo.mark_all_read(user_id)

    async def delete_notification(self, user_id: UUID, id: UUID) -> None:
        deleted = await self.repo.delete(user_id, id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Notification not found")
