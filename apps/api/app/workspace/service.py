from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
import re
from .repository import WorkspaceRepository
from .models import Workspace, WorkspaceMember
from .exceptions import WorkspaceNotFoundError, DuplicateWorkspaceNameError

class WorkspaceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = WorkspaceRepository(db)

    def _generate_slug(self, name: str) -> str:
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s-]+', '-', slug)
        return slug.strip('-')

    async def create_workspace(
        self, name: str, org_id: UUID, user_id: UUID, description: Optional[str] = None,
        icon: Optional[str] = None, color: Optional[str] = None
    ) -> Workspace:
        if await self.repo.exists_by_name(name, org_id):
            raise DuplicateWorkspaceNameError(f"Workspace with name '{name}' already exists in this organization")

        base_slug = self._generate_slug(name)
        slug = base_slug
        counter = 1
        while await self.repo.get_by_slug(slug, org_id):
            slug = f"{base_slug}-{counter}"
            counter += 1

        workspace = await self.repo.create(
            name=name,
            slug=slug,
            org_id=org_id,
            created_by=user_id,
            description=description,
            icon=icon,
            color=color,
            is_default=False,
            is_archived=False
        )

        await self.repo.add_member(workspace.id, user_id, "owner")
        return workspace

    async def get_workspace(self, id: UUID, org_id: UUID) -> Workspace:
        ws = await self.repo.get(id, org_id)
        if not ws:
            raise WorkspaceNotFoundError(f"Workspace not found")
        return ws

    async def update_workspace(
        self, id: UUID, org_id: UUID, name: Optional[str] = None, description: Optional[str] = None,
        icon: Optional[str] = None, color: Optional[str] = None
    ) -> Workspace:
        ws = await self.get_workspace(id, org_id)
        update_data = {}
        if name is not None:
            if name != ws.name:
                if await self.repo.exists_by_name(name, org_id):
                    raise DuplicateWorkspaceNameError(f"Workspace with name '{name}' already exists in this organization")
                update_data["name"] = name
                base_slug = self._generate_slug(name)
                slug = base_slug
                counter = 1
                while await self.repo.get_by_slug(slug, org_id):
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                update_data["slug"] = slug

        if description is not None:
            update_data["description"] = description
        if icon is not None:
            update_data["icon"] = icon
        if color is not None:
            update_data["color"] = color

        if not update_data:
            return ws

        updated = await self.repo.update(id, org_id, **update_data)
        return updated

    async def archive_workspace(self, id: UUID, org_id: UUID) -> Workspace:
        await self.get_workspace(id, org_id)
        updated = await self.repo.update(id, org_id, is_archived=True)
        return updated

    async def restore_workspace(self, id: UUID, org_id: UUID) -> Workspace:
        await self.get_workspace(id, org_id)
        updated = await self.repo.update(id, org_id, is_archived=False)
        return updated

    async def delete_workspace(self, id: UUID, org_id: UUID, soft: bool = True) -> None:
        ws = await self.get_workspace(id, org_id)
        deleted = await self.repo.delete(id, org_id, soft=soft)
        if not deleted:
            raise WorkspaceNotFoundError(f"Workspace not found")

    async def list_workspaces(self, org_id: UUID, user_id: Optional[UUID] = None, include_archived: bool = True) -> List[Workspace]:
        return await self.repo.list(org_id, user_id, include_archived)

    async def get_settings(self, workspace_id: UUID, org_id: UUID) -> WorkspaceSettings:
        await self.get_workspace(workspace_id, org_id)
        settings_obj = await self.repo.get_settings(workspace_id)
        if not settings_obj:
            settings_obj = WorkspaceSettings(workspace_id=workspace_id)
            await self.repo.save_settings(settings_obj)
            await self.db.commit()
        return settings_obj

    async def update_settings(self, workspace_id: UUID, org_id: UUID, update_data: dict) -> WorkspaceSettings:
        settings_obj = await self.get_settings(workspace_id, org_id)
        for key, value in update_data.items():
            if value is not None and hasattr(settings_obj, key):
                setattr(settings_obj, key, value)
        await self.db.commit()
        await self.db.refresh(settings_obj)
        return settings_obj

    async def invite_workspace_member(self, id: UUID, org_id: UUID, user_id: UUID, role: str) -> WorkspaceMember:
        await self.get_workspace(id, org_id)
        return await self.repo.add_member(id, user_id, role.lower())

    async def remove_workspace_member(self, id: UUID, org_id: UUID, target_user_id: UUID) -> bool:
        await self.get_workspace(id, org_id)
        return await self.repo.remove_member(id, target_user_id)

    async def get_workspace_members(self, id: UUID, org_id: UUID):
        await self.get_workspace(id, org_id)
        members_data = await self.repo.list_members(id)
        result = []
        for mem, u in members_data:
            result.append({
                "id": mem.id,
                "workspace_id": mem.workspace_id,
                "user_id": mem.user_id,
                "role": mem.role,
                "status": mem.status,
                "joined_at": mem.joined_at,
                "username": u.username,
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "avatar_url": u.avatar_url
            })
        return result

