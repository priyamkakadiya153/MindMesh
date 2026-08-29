from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from ..core.database import get_db_session
from ..authorization.organization_resolver import resolve_organization_id
from .service import ProjectService
from .models import Project

async def get_current_project(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
) -> Project:
    service = ProjectService(db)
    return await service.get_project(id, org_id)
