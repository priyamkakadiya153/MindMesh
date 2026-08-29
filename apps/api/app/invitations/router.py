from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from sqlalchemy import select
from ..core.database import get_db_session
from ..auth.dependencies import get_current_user
from ..models.user import User
from ..models.organization import OrganizationInvitation
from ..organizations.service import OrganizationService
from ..organizations.schemas import InvitationResponse

router = APIRouter()
org_service = OrganizationService()

@router.get("", response_model=List[InvitationResponse])
@router.get("/", response_model=List[InvitationResponse])
@router.get("/my", response_model=List[InvitationResponse])
async def list_my_invitations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    invites = await org_service.repo.list_user_invitations(db, current_user.email)
    result = []
    for inv in invites:
        res_dict = InvitationResponse.model_validate(inv)
        if inv.organization:
            res_dict.org_name = inv.organization.name
        result.append(res_dict)
    return result

@router.post("/{invite_id_or_token}/accept")
async def accept_invitation(
    invite_id_or_token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await org_service.accept_invitation(db, invite_id_or_token, current_user)

@router.post("/{invite_id_or_token}/decline")
@router.post("/{invite_id_or_token}/reject")
async def reject_invitation(
    invite_id_or_token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        invite_id = UUID(invite_id_or_token)
        return await org_service.reject_invitation(db, invite_id, current_user)
    except ValueError:
        # If token provided instead of UUID
        stmt = select(OrganizationInvitation).where(
            OrganizationInvitation.token == invite_id_or_token,
            OrganizationInvitation.deleted_at == None
        )
        res = await db.execute(stmt)
        inv = res.scalar_one_or_none()
        if not inv:
            raise HTTPException(status_code=404, detail="Invitation not found")
        return await org_service.reject_invitation(db, inv.id, current_user)
