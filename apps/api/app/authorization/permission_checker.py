from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from ..core.database import get_db_session
from ..auth.dependencies import get_current_user
from ..models.user import User
from .organization_resolver import resolve_organization_id
from ..permissions.service import PermissionService

perm_service = PermissionService()

class PermissionChecker:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        org_id: UUID = Depends(resolve_organization_id),
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        db: AsyncSession = Depends(get_db_session)
    ) -> None:
        await perm_service.require_permission(
            db, current_user.id, org_id, self.required_permission, workspace_id, project_id
        )

def require_permission(permission_name: str):
    return PermissionChecker(permission_name)
