from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List, Optional
from ..models.role import Role

class RoleRepository:
    async def get_role(self, db: AsyncSession, role_id: UUID) -> Optional[Role]:
        stmt = select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id, Role.deleted_at == None)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_role_by_name(self, db: AsyncSession, name: str) -> Optional[Role]:
        stmt = select(Role).options(selectinload(Role.permissions)).where(Role.name == name, Role.deleted_at == None)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_roles(self, db: AsyncSession) -> List[Role]:
        stmt = select(Role).options(selectinload(Role.permissions)).where(Role.deleted_at == None)
        res = await db.execute(stmt)
        return list(res.scalars().all())
