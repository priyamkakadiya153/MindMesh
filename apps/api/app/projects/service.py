from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
import re
from datetime import datetime
from sqlalchemy import select, func
from .repository import ProjectRepository
from .models import Project, ProjectMember, ProjectSettings
from .exceptions import ProjectNotFoundError, DuplicateProjectNameError
from ..workspace.service import WorkspaceService
from ..models.document import Document
from ..models.chat import Chat
from ..models.task import Task
from ..models.audit import AuditLog
from ..models.user import User
from fastapi import HTTPException, status

class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProjectRepository(db)
        self.ws_service = WorkspaceService(db)

    def _generate_slug(self, name: str) -> str:
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s-]+', '-', slug)
        return slug.strip('-') or 'project'

    async def create_project(
        self, name: str, workspace_id: UUID, org_id: UUID, user_id: UUID,
        slug: Optional[str] = None, description: Optional[str] = None, icon: Optional[str] = None,
        color: Optional[str] = "#3B82F6", visibility: str = "private", status_val: str = "active",
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Project:
        await self.ws_service.get_workspace(workspace_id, org_id)

        if await self.repo.exists_by_name(name, workspace_id, org_id):
            raise DuplicateProjectNameError(f"Project with name '{name}' already exists in this workspace")

        base_slug = slug or self._generate_slug(name)
        final_slug = base_slug
        counter = 1
        while await self.repo.get_by_slug(final_slug, workspace_id, org_id):
            final_slug = f"{base_slug}-{counter}"
            counter += 1

        project = await self.repo.create(
            name=name,
            slug=final_slug,
            workspace_id=workspace_id,
            org_id=org_id,
            owner_id=user_id,
            description=description,
            icon=icon,
            color=color or "#3B82F6",
            visibility=visibility,
            status=status_val,
            start_date=start_date,
            end_date=end_date,
            is_archived=False
        )

        audit = AuditLog(
            action="Project Created",
            user_id=user_id,
            organization_id=org_id,
            details={
                "project_id": str(project.id),
                "project_name": project.name,
                "workspace_id": str(workspace_id)
            }
        )
        self.db.add(audit)

        return project

    async def get_project(self, id: UUID, org_id: UUID) -> Project:
        proj = await self.repo.get(id, org_id)
        if not proj:
            raise ProjectNotFoundError("Project not found")
        return proj

    async def update_project(
        self, id: UUID, org_id: UUID, name: Optional[str] = None, slug: Optional[str] = None,
        description: Optional[str] = None, icon: Optional[str] = None, color: Optional[str] = None,
        visibility: Optional[str] = None, status_val: Optional[str] = None,
        default_ai_model: Optional[str] = None, start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Project:
        proj = await self.get_project(id, org_id)
        update_data = {}

        if name is not None and name != proj.name:
            if await self.repo.exists_by_name(name, proj.workspace_id, org_id):
                raise DuplicateProjectNameError(f"Project with name '{name}' already exists in this workspace")
            update_data["name"] = name
            if not slug:
                base_slug = self._generate_slug(name)
                final_slug = base_slug
                counter = 1
                while await self.repo.get_by_slug(final_slug, proj.workspace_id, org_id):
                    final_slug = f"{base_slug}-{counter}"
                    counter += 1
                update_data["slug"] = final_slug

        if slug is not None and slug != proj.slug:
            update_data["slug"] = slug
        if description is not None:
            update_data["description"] = description
        if icon is not None:
            update_data["icon"] = icon
        if color is not None:
            update_data["color"] = color
        if visibility is not None:
            update_data["visibility"] = visibility
        if status_val is not None:
            update_data["status"] = status_val
            if status_val == "archived":
                update_data["is_archived"] = True
            elif status_val == "active":
                update_data["is_archived"] = False
        if default_ai_model is not None:
            update_data["default_ai_model"] = default_ai_model
        if start_date is not None:
            update_data["start_date"] = start_date
        if end_date is not None:
            update_data["end_date"] = end_date

        if not update_data:
            return proj

        return await self.repo.update(id, org_id, **update_data)

    async def archive_project(self, id: UUID, org_id: UUID) -> Project:
        await self.get_project(id, org_id)
        proj = await self.repo.archive(id, org_id)
        if not proj:
            raise ProjectNotFoundError("Project not found")
        return proj

    async def restore_project(self, id: UUID, org_id: UUID) -> Project:
        await self.get_project(id, org_id)
        proj = await self.repo.restore(id, org_id)
        if not proj:
            raise ProjectNotFoundError("Project not found")
        return proj

    async def delete_project(self, id: UUID, org_id: UUID, soft: bool = True) -> None:
        await self.get_project(id, org_id)
        deleted = await self.repo.delete(id, org_id, soft=soft)
        if not deleted:
            raise ProjectNotFoundError("Project not found")

    async def list_projects(self, org_id: UUID, workspace_id: Optional[UUID] = None, status_val: Optional[str] = None, search: Optional[str] = None, include_archived: bool = True) -> List[Project]:
        return await self.repo.list(org_id, workspace_id, status=status_val, search=search, include_archived=include_archived)

    # Settings
    async def get_settings(self, project_id: UUID, org_id: UUID) -> ProjectSettings:
        await self.get_project(project_id, org_id)
        settings = await self.repo.get_settings(project_id)
        if not settings:
            settings = await self.repo.update_settings(project_id)
        return settings

    async def update_settings(self, project_id: UUID, org_id: UUID, **kwargs) -> ProjectSettings:
        await self.get_project(project_id, org_id)
        return await self.repo.update_settings(project_id, **kwargs)

    # Roster Management
    async def add_project_member(self, project_id: UUID, org_id: UUID, email: str, role: str) -> ProjectMember:
        await self.get_project(project_id, org_id)
        stmt = select(User).where(User.email == email)
        res = await self.db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email not found")

        return await self.repo.add_member(project_id, user.id, role)

    async def update_project_member(self, project_id: UUID, org_id: UUID, user_id: UUID, role: Optional[str] = None, status_val: Optional[str] = None) -> ProjectMember:
        await self.get_project(project_id, org_id)
        member = await self.repo.update_member(project_id, user_id, role=role, status=status_val)
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found")
        return member

    async def remove_project_member(self, project_id: UUID, org_id: UUID, user_id: UUID) -> None:
        await self.get_project(project_id, org_id)
        removed = await self.repo.remove_member(project_id, user_id)
        if not removed:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found")

    async def get_project_members(self, project_id: UUID, org_id: UUID):
        await self.get_project(project_id, org_id)
        members_data = await self.repo.list_members(project_id)
        return [
            {
                "id": mem.id,
                "project_id": mem.project_id,
                "user_id": mem.user_id,
                "role": mem.role,
                "status": mem.status,
                "joined_at": mem.joined_at,
                "username": u.username,
                "email": u.email
            }
            for mem, u in members_data
        ]

    # Dashboard & Overview
    async def get_dashboard(self, project_id: UUID, org_id: UUID) -> dict:
        proj = await self.get_project(project_id, org_id)

        stmt_mem = select(func.count(ProjectMember.id)).where(ProjectMember.project_id == project_id, ProjectMember.is_active == True)
        member_count = (await self.db.execute(stmt_mem)).scalar() or 0

        stmt_doc = select(func.count(Document.id)).where(Document.project_id == project_id, Document.is_active == True)
        document_count = (await self.db.execute(stmt_doc)).scalar() or 0

        stmt_chat = select(func.count(Chat.id)).where(Chat.workspace_id == proj.workspace_id, Chat.is_active == True)
        chat_count = (await self.db.execute(stmt_chat)).scalar() or 0

        stmt_task = select(func.count(Task.id)).where(Task.project_id == project_id, Task.is_active == True)
        task_count = (await self.db.execute(stmt_task)).scalar() or 0

        return {
            "project": proj,
            "member_count": member_count,
            "document_count": document_count,
            "chat_count": chat_count,
            "task_count": task_count,
            "recent_activity": [
                {"action": "Project Created", "timestamp": proj.created_at.isoformat(), "details": f"Created by {proj.owner.username if proj.owner else 'Owner'}"}
            ]
        }

    async def get_project_statistics(self, project_id: UUID, org_id: UUID) -> dict:
        proj = await self.get_project(project_id, org_id)

        stmt_mem = select(func.count(ProjectMember.id)).where(ProjectMember.project_id == project_id, ProjectMember.is_active == True)
        member_count = (await self.db.execute(stmt_mem)).scalar() or 0

        stmt_doc = select(func.count(Document.id)).where(Document.project_id == project_id, Document.is_active == True)
        document_count = (await self.db.execute(stmt_doc)).scalar() or 0

        stmt_chat = select(func.count(Chat.id)).where(Chat.workspace_id == proj.workspace_id, Chat.is_active == True)
        chat_count = (await self.db.execute(stmt_chat)).scalar() or 0

        return {
            "member_count": member_count,
            "document_count": document_count,
            "chat_count": chat_count,
            "storage_used": 0
        }
