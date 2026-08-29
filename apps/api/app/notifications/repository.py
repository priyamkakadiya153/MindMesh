from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc, and_, func
from uuid import UUID
from typing import List, Optional
from datetime import datetime
from .models import Notification

class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
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
        notif = Notification(
            user_id=user_id,
            organization_id=organization_id,
            title=title,
            message=message,
            type=type,
            priority=priority,
            is_read=False,
            link=link,
            entity_type=entity_type,
            entity_id=entity_id
        )
        self.session.add(notif)
        await self.session.flush()
        return notif

    async def list_for_user(self, user_id: UUID, limit: int = 50, offset: int = 0, only_unread: bool = False) -> List[Notification]:
        cond = [
            Notification.user_id == user_id,
            Notification.is_active == True
        ]
        if only_unread:
            cond.append(Notification.is_read == False)
        stmt = (
            select(Notification)
            .where(and_(*cond))
            .order_by(desc(Notification.created_at))
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_unread_count(self, user_id: UUID) -> int:
        stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read == False,
            Notification.is_active == True
        )
        res = await self.session.execute(stmt)
        return res.scalar_one() or 0

    async def mark_read(self, user_id: UUID, id: UUID) -> Optional[Notification]:
        stmt = (
            update(Notification)
            .where(Notification.id == id, Notification.user_id == user_id)
            .values(is_read=True, updated_at=datetime.utcnow())
            .returning(Notification)
        )
        res = await self.session.execute(stmt)
        return res.scalar()

    async def mark_read_by_entity(self, user_id: UUID, entity_type: str, entity_id: UUID) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.entity_type == entity_type,
                Notification.entity_id == entity_id,
                Notification.is_read == False
            )
            .values(is_read=True, updated_at=datetime.utcnow())
        )
        res = await self.session.execute(stmt)
        return res.rowcount or 0

    async def mark_all_read(self, user_id: UUID) -> int:
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True, updated_at=datetime.utcnow())
        )
        res = await self.session.execute(stmt)
        return res.rowcount or 0

    async def delete(self, user_id: UUID, id: UUID) -> bool:
        stmt = delete(Notification).where(Notification.id == id, Notification.user_id == user_id)
        res = await self.session.execute(stmt)
        return (res.rowcount or 0) > 0
