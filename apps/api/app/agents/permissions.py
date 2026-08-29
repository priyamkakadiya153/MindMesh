from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.workspace.models import Workspace, WorkspaceMember
from app.projects.models import Project, ProjectMember
from app.models.organization_member import OrganizationMember
from app.agents.context import SessionContext
from app.agents.exceptions import PermissionDeniedException

class AgentPermissionValidator:
    @staticmethod
    async def validate_context_access(db: AsyncSession, context: SessionContext) -> bool:
        """Validates organization, workspace, and project isolation for the session context."""
        # 1. Organization Member check
        org_stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == context.organization_id,
            OrganizationMember.user_id == context.user_id
        )
        org_res = await db.execute(org_stmt)
        if not org_res.scalar_one_or_none():
            raise PermissionDeniedException(f"User {context.user_id} is not a member of organization {context.organization_id}")

        # 2. Workspace checks (if workspace_id is provided)
        if context.workspace_id:
            ws_stmt = select(Workspace).where(Workspace.id == context.workspace_id)
            ws_res = await db.execute(ws_stmt)
            ws = ws_res.scalar_one_or_none()
            if not ws:
                raise PermissionDeniedException(f"Workspace {context.workspace_id} not found")
            if ws.organization_id != context.organization_id:
                raise PermissionDeniedException(f"Workspace {context.workspace_id} does not belong to organization {context.organization_id}")

            ws_mem_stmt = select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == context.workspace_id,
                WorkspaceMember.user_id == context.user_id
            )
            ws_mem_res = await db.execute(ws_mem_stmt)
            if not ws_mem_res.scalar_one_or_none():
                raise PermissionDeniedException(f"User {context.user_id} is not a member of workspace {context.workspace_id}")

        # 3. Project checks (if project_id is provided)
        if context.project_id:
            proj_stmt = select(Project).where(Project.id == context.project_id)
            proj_res = await db.execute(proj_stmt)
            proj = proj_res.scalar_one_or_none()
            if not proj:
                raise PermissionDeniedException(f"Project {context.project_id} not found")
            if proj.organization_id != context.organization_id:
                raise PermissionDeniedException(f"Project {context.project_id} does not belong to organization {context.organization_id}")
            if context.workspace_id and proj.workspace_id != context.workspace_id:
                raise PermissionDeniedException(f"Project {context.project_id} does not belong to workspace {context.workspace_id}")

            proj_mem_stmt = select(ProjectMember).where(
                ProjectMember.project_id == context.project_id,
                ProjectMember.user_id == context.user_id
            )
            proj_mem_res = await db.execute(proj_mem_stmt)
            if not proj_mem_res.scalar_one_or_none():
                raise PermissionDeniedException(f"User {context.user_id} is not a member of project {context.project_id}")

        return True

    @staticmethod
    async def validate_tool_permission(db: AsyncSession, context: SessionContext, required_permissions: list[str]) -> bool:
        """Validates if the user has specific tool permissions in context."""
        # Ensure context has basic organization/workspace access
        await AgentPermissionValidator.validate_context_access(db, context)

        if not required_permissions:
            return True

        # Check if context permissions contain all required permissions
        # If context has a wild card or explicit matches:
        if "*" in context.permissions:
            return True

        for perm in required_permissions:
            if perm not in context.permissions:
                return False
        return True
