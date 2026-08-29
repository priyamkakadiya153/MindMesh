from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from uuid import UUID
from typing import List, Optional
from ..models.favorite import Favorite

class FavoriteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_favorite(
        self, user_id: UUID, entity_type: str, entity_id: UUID, name: str, slug: Optional[str] = None
    ) -> Favorite:
        stmt = select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.item_type == entity_type,
            Favorite.item_id == str(entity_id)
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        fav = Favorite(
            user_id=user_id,
            item_type=entity_type,
            item_id=str(entity_id),
            name=name,
            slug=slug
        )
        self.db.add(fav)
        await self.db.flush()
        return fav

    async def remove_favorite(self, user_id: UUID, entity_type: str, entity_id: UUID) -> bool:
        stmt = delete(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.item_type == entity_type,
            Favorite.item_id == str(entity_id)
        )
        res = await self.db.execute(stmt)
        return (res.rowcount or 0) > 0

    async def remove_favorite_by_id(self, user_id: UUID, id: UUID) -> bool:
        stmt = delete(Favorite).where(
            Favorite.id == id,
            Favorite.user_id == user_id
        )
        res = await self.db.execute(stmt)
        return (res.rowcount or 0) > 0

    async def list_favorites(self, user_id: UUID) -> List[Favorite]:
        stmt = select(Favorite).where(Favorite.user_id == user_id, Favorite.is_active == True)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
