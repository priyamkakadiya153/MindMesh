from typing import Generic, Type, TypeVar, Optional, List, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
from ..database.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id, self.model.deleted_at == None)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        stmt = select(self.model).where(self.model.deleted_at == None).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: ModelType) -> ModelType:
        db.add(obj_in)
        await db.flush()
        return obj_in

    async def update(self, db: AsyncSession, *, db_obj: ModelType, update_data: dict) -> ModelType:
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        await db.flush()
        return db_obj

    async def remove(self, db: AsyncSession, *, id: UUID) -> Optional[ModelType]:
        obj = await self.get(db, id)
        if obj:
            obj.deleted_at = datetime.utcnow()
            obj.is_active = False
            db.add(obj)
            await db.flush()
        return obj
