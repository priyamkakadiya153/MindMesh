from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from ..core.database import get_db_session
from ..authorization.organization_resolver import resolve_organization_id
from .service import WorkspaceService
from .models import Workspace

async def get_current_workspace(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
) -> Workspace:
    service = WorkspaceService(db)
    return await service.get_workspace(id, org_id)
