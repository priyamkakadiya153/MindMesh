from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from uuid import UUID
from typing import List, Optional, Set

from ..models.organization_member import OrganizationMember
from ..workspace.models import WorkspaceMember
from ..projects.models import ProjectMember
from ..models.role import Role
from ..models.permission import Permission

ROLE_PERMISSION_MAP: dict[str, set[str]] = {
    "owner": {
        "*"
    },
    "admin": {
        "organization.edit", "organization.view",
        "workspace.create", "workspace.edit", "workspace.delete", "workspace.view",
        "project.create", "project.edit", "project.delete", "project.view",
        "member.invite", "member.remove", "member.promote", "member.demote", "member.view",
        "settings.update", "analytics.view",
        "messages.create", "messages.read", "messages.delete",
        "files.upload", "files.download", "files.delete",
        "knowledge.search", "knowledge.manage",
        "ai.prompt", "ai.agents"
    },
    "manager": {
        "organization.view",
        "workspace.edit", "workspace.view",
        "project.create", "project.edit", "project.view",
        "member.invite", "member.view",
        "settings.update", "analytics.view",
        "messages.create", "messages.read",
        "files.upload", "files.download",
        "knowledge.search", "knowledge.manage",
        "ai.prompt"
    },
    "contributor": {
        "organization.view",
        "workspace.view",
        "project.edit", "project.view",
        "member.view",
        "messages.create", "messages.read",
        "files.upload", "files.download",
        "knowledge.search",
        "ai.prompt"
    },
    "member": {
        "organization.view",
        "workspace.view",
        "project.view",
        "member.view",
        "messages.create", "messages.read",
        "files.upload", "files.download",
        "knowledge.search",
        "ai.prompt"
    },
    "guest": {
        "organization.view",
        "workspace.view",
        "project.view",
        "messages.read",
        "files.download",
        "knowledge.search"
    },
    "viewer": {
        "organization.view",
        "workspace.view",
        "project.view",
        "messages.read",
        "files.download",
        "knowledge.search"
    }
}

class PermissionService:
    async def get_user_effective_permissions(
        self, db: AsyncSession, user_id: UUID, org_id: UUID,
        workspace_id: Optional[UUID] = None, project_id: Optional[UUID] = None
    ) -> Set[str]:
        perms: Set[str] = set()

        # 1. Organization Role
        org_stmt = select(OrganizationMember.role, OrganizationMember.status).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
            OrganizationMember.deleted_at.is_(None)
        )
        org_res = await db.execute(org_stmt)
        org_row = org_res.first()

        if not org_row or org_row.status == "suspended":
            return perms

        org_role = (org_row.role or "member").lower()
        perms.update(ROLE_PERMISSION_MAP.get(org_role, set()))

        # If owner, has full wildcards
        if "*" in perms:
            return perms

        # 2. Workspace Role if specified
        if workspace_id:
            ws_stmt = select(WorkspaceMember.role).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.is_active == True
            )
            ws_res = await db.execute(ws_stmt)
            ws_role = ws_res.scalar_one_or_none()
            if ws_role:
                perms.update(ROLE_PERMISSION_MAP.get(ws_role.lower(), set()))

        # 3. Project Role if specified
        if project_id:
            proj_stmt = select(ProjectMember.role).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
                ProjectMember.is_active == True
            )
            proj_res = await db.execute(proj_stmt)
            proj_role = proj_res.scalar_one_or_none()
            if proj_role:
                perms.update(ROLE_PERMISSION_MAP.get(proj_role.lower(), set()))

        return perms

    async def has_permission(
        self, db: AsyncSession, user_id: UUID, org_id: UUID, permission_name: str,
        workspace_id: Optional[UUID] = None, project_id: Optional[UUID] = None
    ) -> bool:
        effective = await self.get_user_effective_permissions(db, user_id, org_id, workspace_id, project_id)
        if "*" in effective or permission_name in effective:
            return True

        category = permission_name.split(".")[0] if "." in permission_name else None
        if category and f"{category}.*" in effective:
            return True

        return False

    async def require_permission(
        self, db: AsyncSession, user_id: UUID, org_id: UUID, permission_name: str,
        workspace_id: Optional[UUID] = None, project_id: Optional[UUID] = None
    ) -> None:
        allowed = await self.has_permission(db, user_id, org_id, permission_name, workspace_id, project_id)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: '{permission_name}'"
            )

    async def require_role(self, db: AsyncSession, user_id: UUID, org_id: UUID, role_name: str) -> None:
        stmt = select(OrganizationMember.role).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
            OrganizationMember.deleted_at.is_(None)
        )
        res = await db.execute(stmt)
        user_role = res.scalar_one_or_none()
        if not user_role or user_role.lower() != role_name.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required role: '{role_name}'"
            )

    def can_access_resource(self, resource_org_id: UUID, target_org_id: UUID) -> bool:
        return resource_org_id == target_org_id
