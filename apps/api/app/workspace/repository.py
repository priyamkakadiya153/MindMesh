from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, exists
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List, Optional
from datetime import datetime
from .models import Workspace, WorkspaceMember, WorkspaceSettings
from ..models.user import User

class WorkspaceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, slug: str, org_id: UUID, created_by: Optional[UUID] = None, **kwargs) -> Workspace:
        workspace = Workspace(
            name=name,
            slug=slug,
            organization_id=org_id,
            created_by=created_by,
            **kwargs
        )
        self.session.add(workspace)
        await self.session.flush()
        workspace.settings = None
        return workspace

    async def get(self, id: UUID, org_id: UUID) -> Optional[Workspace]:
        stmt = (
            select(Workspace)
            .options(selectinload(Workspace.settings))
            .where(
                Workspace.id == id,
                Workspace.organization_id == org_id,
                Workspace.is_active == True,
                Workspace.deleted_at.is_(None)
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_slug(self, slug: str, org_id: UUID) -> Optional[Workspace]:
        stmt = (
            select(Workspace)
            .options(selectinload(Workspace.settings))
            .where(
                Workspace.slug == slug,
                Workspace.organization_id == org_id,
                Workspace.is_active == True,
                Workspace.deleted_at.is_(None)
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def update(self, id: UUID, org_id: UUID, **kwargs) -> Optional[Workspace]:
        ws = await self.get(id, org_id)
        if not ws:
            return None
        for key, value in kwargs.items():
            if hasattr(ws, key):
                setattr(ws, key, value)
        ws.updated_at = datetime.utcnow()
        await self.session.commit()
        return ws

    async def delete(self, id: UUID, org_id: UUID, soft: bool = True) -> bool:
        ws = await self.get(id, org_id)
        if not ws:
            return False
        if soft:
            ws.is_active = False
            ws.deleted_at = datetime.utcnow()
            await self.session.commit()
            return True
        else:
            await self.session.delete(ws)
            await self.session.commit()
            return True

    async def list(self, org_id: UUID, user_id: Optional[UUID] = None, include_archived: bool = True) -> List[Workspace]:
        cond = [
            Workspace.organization_id == org_id,
            Workspace.is_active == True,
            Workspace.deleted_at.is_(None)
        ]
        if not include_archived:
            cond.append(Workspace.is_archived == False)
            
        stmt = (
            select(Workspace)
            .options(selectinload(Workspace.settings))
            .where(and_(*cond))
        )
        if user_id:
            stmt = (
                stmt.join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
                .where(
                    WorkspaceMember.user_id == user_id,
                    WorkspaceMember.is_active == True
                )
            )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def exists(self, id: UUID, org_id: UUID) -> bool:
        stmt = select(exists().where(
            Workspace.id == id,
            Workspace.organization_id == org_id,
            Workspace.is_active == True,
            Workspace.deleted_at.is_(None)
        ))
        res = await self.session.execute(stmt)
        return bool(res.scalar())

    async def exists_by_name(self, name: str, org_id: UUID) -> bool:
        stmt = select(exists().where(
            Workspace.name == name,
            Workspace.organization_id == org_id,
            Workspace.is_active == True,
            Workspace.deleted_at.is_(None)
        ))
        res = await self.session.execute(stmt)
        return bool(res.scalar())

    async def get_settings(self, workspace_id: UUID) -> Optional[WorkspaceSettings]:
        stmt = select(WorkspaceSettings).where(WorkspaceSettings.workspace_id == workspace_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def save_settings(self, settings: WorkspaceSettings) -> WorkspaceSettings:
        self.session.add(settings)
        await self.session.flush()
        return settings

    async def get_member(self, workspace_id: UUID, user_id: UUID) -> Optional[WorkspaceMember]:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.deleted_at.is_(None)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def add_member(self, workspace_id: UUID, user_id: UUID, role: str) -> WorkspaceMember:
        existing = await self.get_member(workspace_id, user_id)
        if existing:
            existing.role = role
            return existing

        member = WorkspaceMember(workspace_id=workspace_id, user_id=user_id, role=role, status="active")
        self.session.add(member)
        await self.session.flush()
        return member

    async def remove_member(self, workspace_id: UUID, user_id: UUID) -> bool:
        member = await self.get_member(workspace_id, user_id)
        if member:
            await self.session.delete(member)
            await self.session.commit()
            return True
        return False

    async def list_members(self, workspace_id: UUID) -> List[tuple[WorkspaceMember, User]]:
        stmt = (
            select(WorkspaceMember, User)
            .join(User, WorkspaceMember.user_id == User.id)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.is_active == True
            )
        )
        res = await self.session.execute(stmt)
        return list(res.all())

