from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, exists
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timezone
from .models import Project, ProjectMember, ProjectSettings
from ..models.user import User

class ProjectRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, slug: str, workspace_id: UUID, org_id: UUID, owner_id: UUID, **kwargs) -> Project:
        project = Project(
            name=name,
            slug=slug,
            workspace_id=workspace_id,
            organization_id=org_id,
            owner_id=owner_id,
            created_by=str(owner_id) if owner_id else None,
            **kwargs
        )
        self.session.add(project)
        await self.session.flush()

        # Create default ProjectSettings
        settings = ProjectSettings(project_id=project.id, created_by=str(owner_id) if owner_id else None)
        self.session.add(settings)

        # Automatically add owner as 'owner' member
        owner_member = ProjectMember(project_id=project.id, user_id=owner_id, role="owner", status="active")
        self.session.add(owner_member)
        await self.session.flush()
        project.settings = settings
        return project

    async def get(self, id: UUID, org_id: UUID) -> Optional[Project]:
        stmt = (
            select(Project)
            .options(selectinload(Project.settings), selectinload(Project.owner))
            .where(
                Project.id == id,
                Project.organization_id == org_id,
                Project.is_active == True,
                Project.deleted_at.is_(None)
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_slug(self, slug: str, workspace_id: UUID, org_id: UUID) -> Optional[Project]:
        stmt = (
            select(Project)
            .options(selectinload(Project.settings), selectinload(Project.owner))
            .where(
                Project.slug == slug,
                Project.workspace_id == workspace_id,
                Project.organization_id == org_id,
                Project.is_active == True,
                Project.deleted_at.is_(None)
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def update(self, id: UUID, org_id: UUID, **kwargs) -> Optional[Project]:
        project = await self.get(id, org_id)
        if not project:
            return None
        for key, val in kwargs.items():
            if val is not None and hasattr(project, key):
                setattr(project, key, val)
        project.updated_at = datetime.utcnow()
        await self.session.flush()
        return project

    async def delete(self, id: UUID, org_id: UUID, soft: bool = True) -> bool:
        project = await self.get(id, org_id)
        if not project:
            return False
        if soft:
            project.is_active = False
            project.deleted_at = datetime.utcnow()
        else:
            await self.session.delete(project)
        await self.session.flush()
        return True

    async def archive(self, id: UUID, org_id: UUID) -> Optional[Project]:
        project = await self.get(id, org_id)
        if not project:
            return None
        project.is_archived = True
        project.status = "archived"
        project.updated_at = datetime.utcnow()
        await self.session.flush()
        return project

    async def restore(self, id: UUID, org_id: UUID) -> Optional[Project]:
        project = await self.get(id, org_id)
        if not project:
            return None
        project.is_archived = False
        project.status = "active"
        project.updated_at = datetime.utcnow()
        await self.session.flush()
        return project

    async def list(self, org_id: UUID, workspace_id: Optional[UUID] = None, status: Optional[str] = None, search: Optional[str] = None, include_archived: bool = True) -> List[Project]:
        cond = [
            Project.organization_id == org_id,
            Project.is_active == True,
            Project.deleted_at.is_(None)
        ]
        if workspace_id:
            cond.append(Project.workspace_id == workspace_id)
        if status:
            cond.append(Project.status == status)
        if not include_archived:
            cond.append(Project.is_archived == False)
        if search and search.strip():
            term = f"%{search.strip()}%"
            cond.append(or_(Project.name.ilike(term), Project.slug.ilike(term), Project.description.ilike(term)))

        stmt = (
            select(Project)
            .options(selectinload(Project.settings), selectinload(Project.owner))
            .where(and_(*cond))
            .order_by(Project.updated_at.desc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def exists_by_name(self, name: str, workspace_id: UUID, org_id: UUID) -> bool:
        stmt = select(exists().where(
            Project.name == name,
            Project.workspace_id == workspace_id,
            Project.organization_id == org_id,
            Project.is_active == True,
            Project.deleted_at.is_(None)
        ))
        res = await self.session.execute(stmt)
        return bool(res.scalar())

    # Settings CRUD
    async def get_settings(self, project_id: UUID) -> Optional[ProjectSettings]:
        stmt = select(ProjectSettings).where(ProjectSettings.project_id == project_id, ProjectSettings.is_active == True)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def update_settings(self, project_id: UUID, **kwargs) -> Optional[ProjectSettings]:
        settings = await self.get_settings(project_id)
        if not settings:
            settings = ProjectSettings(project_id=project_id)
            self.session.add(settings)
            await self.session.flush()

        for key, val in kwargs.items():
            if val is not None and hasattr(settings, key):
                setattr(settings, key, val)
        settings.updated_at = datetime.utcnow()
        await self.session.flush()
        return settings

    # Member Operations
    async def add_member(self, project_id: UUID, user_id: UUID, role: str) -> ProjectMember:
        stmt = select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        res = await self.session.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            existing.role = role.lower()
            existing.status = "active"
            existing.is_active = True
            await self.session.flush()
            return existing

        member = ProjectMember(project_id=project_id, user_id=user_id, role=role.lower(), status="active")
        self.session.add(member)
        await self.session.flush()
        return member

    async def get_member_by_user(self, project_id: UUID, user_id: UUID) -> Optional[ProjectMember]:
        stmt = select(ProjectMember).where(
            ProjectMember.user_id == user_id,
            ProjectMember.project_id == project_id,
            ProjectMember.is_active == True
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def update_member(self, project_id: UUID, user_id: UUID, role: Optional[str] = None, status: Optional[str] = None) -> Optional[ProjectMember]:
        member = await self.get_member_by_user(project_id, user_id)
        if not member:
            return None
        if role:
            member.role = role.lower()
        if status:
            member.status = status
        member.updated_at = datetime.utcnow()
        await self.session.flush()
        return member

    async def remove_member(self, project_id: UUID, user_id: UUID) -> bool:
        stmt = delete(ProjectMember).where(
            ProjectMember.user_id == user_id,
            ProjectMember.project_id == project_id
        )
        res = await self.session.execute(stmt)
        return (res.rowcount or 0) > 0

    async def list_members(self, project_id: UUID) -> List[tuple[ProjectMember, User]]:
        stmt = (
            select(ProjectMember, User)
            .join(User, ProjectMember.user_id == User.id)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.is_active == True
            )
        )
        res = await self.session.execute(stmt)
        return list(res.all())
