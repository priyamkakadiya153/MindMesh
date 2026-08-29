from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from uuid import UUID
from typing import List
from .repository import RoleRepository
from ..models.role import Role

class RoleService:
    def __init__(self):
        self.repo = RoleRepository()

    async def get_role(self, db: AsyncSession, role_id: UUID) -> Role:
        role = await self.repo.get_role(db, role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return role

    async def validate_role(self, db: AsyncSession, name: str) -> Role:
        role = await self.repo.get_role_by_name(db, name)
        if not role:
            raise HTTPException(status_code=400, detail="Invalid role name")
        return role

    async def list_roles(self, db: AsyncSession) -> List[Role]:
        return await self.repo.list_roles(db)
