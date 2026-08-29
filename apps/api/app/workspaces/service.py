from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from .repository import WorkspaceRepository
from ..models.workspace import Workspace
from ..models.workspace_member import WorkspaceMember
from ..models.user import User
from fastapi import HTTPException
from sqlalchemy import select

class WorkspaceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = WorkspaceRepository(db)

    async def _populate_metrics(self, ws: Workspace) -> Workspace:
        if not ws:
            return ws
        
        try:
            from ..projects.models import Project
            from ..models.document import Document
            from ..models.workspace_member import WorkspaceMember
            from sqlalchemy import select, func

            proj_stmt = select(func.count(Project.id)).where(Project.workspace_id == ws.id, Project.is_active == True)
            projects_count = (await self.db.execute(proj_stmt)).scalar() or 0

            doc_stmt = select(func.count(Document.id), func.sum(Document.size)).where(Document.workspace_id == ws.id, Document.is_active == True)
            doc_res = (await self.db.execute(doc_stmt)).first()
            documents_count = doc_res[0] if doc_res and doc_res[0] is not None else 0
            storage_used = int(doc_res[1]) if doc_res and doc_res[1] is not None else 0

            mem_stmt = select(func.count(WorkspaceMember.id)).where(WorkspaceMember.workspace_id == ws.id)
            mem_count_raw = (await self.db.execute(mem_stmt)).scalar() or 0
            members_count = max(1, mem_count_raw)

            setattr(ws, "projects_count", projects_count)
            setattr(ws, "documents_count", documents_count)
            setattr(ws, "members_count", members_count)
            setattr(ws, "storage_used", storage_used)
            setattr(ws, "status", "Archived" if getattr(ws, "is_archived", False) else "Active")
        except Exception:
            setattr(ws, "projects_count", 0)
            setattr(ws, "documents_count", 0)
            setattr(ws, "members_count", 1)
            setattr(ws, "storage_used", 0)
            setattr(ws, "status", "Active")

        return ws

    async def create_workspace(self, name: str, slug: str, org_id: UUID, user_id: UUID) -> Workspace:
        workspace = await self.repo.create(name, slug, org_id)
        await self.repo.add_member(workspace.id, user_id, "OWNER")
        return await self._populate_metrics(workspace)

    async def list_workspaces(self, org_id: UUID) -> List[Workspace]:
        workspaces = await self.repo.list_by_org(org_id)
        res = []
        for ws in workspaces:
            res.append(await self._populate_metrics(ws))
        return res

    async def get_workspace(self, id: UUID, org_id: UUID) -> Workspace:
        ws = await self.repo.get_by_id(id, org_id)
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")
        return await self._populate_metrics(ws)

    async def update_workspace(self, id: UUID, org_id: UUID, name: Optional[str] = None, slug: Optional[str] = None) -> Workspace:
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if slug is not None:
            update_data["slug"] = slug
        if not update_data:
            return await self.get_workspace(id, org_id)
        ws = await self.repo.update(id, org_id, **update_data)
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")
        return await self._populate_metrics(ws)

    async def delete_workspace(self, id: UUID, org_id: UUID) -> None:
        deleted = await self.repo.delete(id, org_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Workspace not found")

    async def invite_member(self, workspace_id: UUID, org_id: UUID, email: str, role: str) -> WorkspaceMember:
        await self.get_workspace(workspace_id, org_id)
        stmt = select(User).where(User.email == email)
        res = await self.db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return await self.repo.add_member(workspace_id, user.id, role)

    async def get_members(self, workspace_id: UUID, org_id: UUID):
        await self.get_workspace(workspace_id, org_id)
        members_data = await self.repo.list_members(workspace_id)
        result = []
        for mem, u in members_data:
            result.append({
                "id": mem.id,
                "workspace_id": mem.workspace_id,
                "user_id": mem.user_id,
                "role": mem.role,
                "username": u.username,
                "email": u.email
            })
        return result
