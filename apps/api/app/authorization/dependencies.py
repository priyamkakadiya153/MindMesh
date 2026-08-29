from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from ..core.database import get_db_session
from ..auth.dependencies import get_current_user
from ..models.user import User
from .organization_resolver import resolve_organization_id
from .permission_checker import PermissionChecker
from ..permissions.service import PermissionService

perm_service = PermissionService()

class RoleChecker:
    def __init__(self, required_role: str):
        self.required_role = required_role

    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        org_id: UUID = Depends(resolve_organization_id),
        db: AsyncSession = Depends(get_db_session)
    ) -> None:
        await perm_service.require_role(db, current_user.id, org_id, self.required_role)

def require_permission(permission_name: str):
    return PermissionChecker(permission_name)

def require_role(role_name: str):
    return RoleChecker(role_name)
