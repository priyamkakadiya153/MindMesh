from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from uuid import UUID
from typing import List, Optional
from ..models.workspace import Workspace
from ..models.workspace_member import WorkspaceMember
from ..models.user import User

class WorkspaceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, slug: str, org_id: UUID) -> Workspace:
        workspace = Workspace(name=name, slug=slug, organization_id=org_id)
        self.session.add(workspace)
        await self.session.flush()
        return workspace

    async def list_by_org(self, org_id: UUID) -> List[Workspace]:
        stmt = select(Workspace).where(Workspace.organization_id == org_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_by_id(self, id: UUID, org_id: UUID) -> Optional[Workspace]:
        stmt = select(Workspace).where(Workspace.id == id, Workspace.organization_id == org_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def update(self, id: UUID, org_id: UUID, **kwargs) -> Optional[Workspace]:
        stmt = (
            update(Workspace)
            .where(Workspace.id == id, Workspace.organization_id == org_id)
            .values(**kwargs)
            .returning(Workspace)
        )
        res = await self.session.execute(stmt)
        return res.scalar()

    async def delete(self, id: UUID, org_id: UUID) -> bool:
        stmt = delete(Workspace).where(Workspace.id == id, Workspace.organization_id == org_id)
        res = await self.session.execute(stmt)
        return (res.rowcount or 0) > 0

    async def add_member(self, workspace_id: UUID, user_id: UUID, role: str) -> WorkspaceMember:
        member = WorkspaceMember(workspace_id=workspace_id, user_id=user_id, role=role)
        self.session.add(member)
        await self.session.flush()
        return member

    async def list_members(self, workspace_id: UUID) -> List[tuple[WorkspaceMember, User]]:
        stmt = (
            select(WorkspaceMember, User)
            .join(User, WorkspaceMember.user_id == User.id)
            .where(WorkspaceMember.workspace_id == workspace_id)
        )
        res = await self.session.execute(stmt)
        return list(res.all())
