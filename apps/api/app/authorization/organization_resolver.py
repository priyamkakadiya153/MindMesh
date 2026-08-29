from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from ..core.database import get_db_session
from ..auth.dependencies import get_current_user
from ..models.user import User
from ..organizations.repository import OrganizationRepository

org_repo = OrganizationRepository()

async def resolve_organization_id(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> UUID:
    org_id_header = request.headers.get("X-Organization-ID")
    if org_id_header:
        try:
            return UUID(org_id_header)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid X-Organization-ID format")

    org_id_query = request.query_params.get("organization_id")
    if org_id_query:
        try:
            return UUID(org_id_query)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid organization_id format")

    if current_user.current_organization_id:
        membership = await org_repo.get_membership(db, current_user.current_organization_id, current_user.id)
        if membership:
            return current_user.current_organization_id

    memberships = await org_repo.list_user_organizations(db, current_user.id)
    if not memberships:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to any organization."
        )
    return memberships[0].organization_id

