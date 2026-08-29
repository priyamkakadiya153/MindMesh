from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete
from uuid import UUID
from typing import List, Optional
from datetime import datetime
from ..models.recent_item import RecentItem

class RecentItemService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_recent(
        self, user_id: UUID, entity_type: str, entity_id: UUID, name: str, slug: Optional[str] = None
    ) -> RecentItem:
        stmt = select(RecentItem).where(
            RecentItem.user_id == user_id,
            RecentItem.item_type == entity_type,
            RecentItem.item_id == str(entity_id)
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            await self.db.delete(existing)
            await self.db.flush()

        recent = RecentItem(
            user_id=user_id,
            item_type=entity_type,
            item_id=str(entity_id),
            name=name,
            slug=slug,
            opened_at=datetime.utcnow()
        )
        self.db.add(recent)
        await self.db.flush()
        return recent

    async def list_recent(self, user_id: UUID, limit: int = 10) -> List[RecentItem]:
        stmt = (
            select(RecentItem)
            .where(RecentItem.user_id == user_id, RecentItem.is_active == True)
            .order_by(desc(RecentItem.opened_at))
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def clear_recent(self, user_id: UUID) -> None:
        stmt = delete(RecentItem).where(RecentItem.user_id == user_id)
        await self.db.execute(stmt)
