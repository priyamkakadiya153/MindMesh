from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from sqlalchemy import select, func, String
from sqlalchemy.orm import selectinload

from ..core.database import get_db_session
from ..auth.dependencies import get_current_user
from ..models.user import User
from ..models.organization import OrganizationInvitation
from ..models.invitation import Invitation
from ..organizations.service import OrganizationService
from ..members.service import EnterpriseInvitationService
from ..organizations.schemas import InvitationResponse

router = APIRouter()
org_service = OrganizationService()
invite_service = EnterpriseInvitationService()

@router.get("", response_model=List[InvitationResponse])
@router.get("/", response_model=List[InvitationResponse])
@router.get("/my", response_model=List[InvitationResponse])
async def list_my_invitations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    clean_email = (current_user.email or '').strip().lower()
    
    # 1. Query OrganizationInvitation table
    org_invites = await org_service.repo.list_user_invitations(db, clean_email)
    
    # 2. Query Invitation table
    ent_invites = await invite_service.list_user_invitations(db, clean_email)
    
    result = []
    seen_ids = set()
    
    for inv in org_invites:
        res_dict = InvitationResponse.model_validate(inv)
        if inv.organization:
            res_dict.org_name = inv.organization.name
        result.append(res_dict)
        seen_ids.add(str(inv.id))
        if inv.token:
            seen_ids.add(inv.token)
            
    for inv in ent_invites:
        if str(inv.id) in seen_ids or (inv.token and inv.token in seen_ids):
            continue
        res_dict = InvitationResponse.model_validate(inv)
        if inv.organization:
            res_dict.org_name = inv.organization.name
        if inv.workspace:
            res_dict.workspace_name = inv.workspace.name
        if inv.project:
            res_dict.project_name = inv.project.name
        result.append(res_dict)
        seen_ids.add(str(inv.id))
        if inv.token:
            seen_ids.add(inv.token)
            
    return result

@router.post("/{invite_id_or_token}/accept")
async def accept_invitation(
    invite_id_or_token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        return await org_service.accept_invitation(db, invite_id_or_token, current_user)
    except HTTPException as e:
        if e.status_code in (400, 404):
            try:
                return await invite_service.accept_invitation(db, invite_id_or_token, current_user)
            except HTTPException:
                raise e
        raise e

@router.post("/{invite_id_or_token}/decline")
@router.post("/{invite_id_or_token}/reject")
async def reject_invitation(
    invite_id_or_token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        invite_id = UUID(invite_id_or_token)
        try:
            return await org_service.reject_invitation(db, invite_id, current_user)
        except HTTPException:
            return await invite_service.reject_invitation(db, invite_id, current_user)
    except ValueError:
        # If token provided instead of UUID
        stmt1 = select(OrganizationInvitation).where(
            OrganizationInvitation.token == invite_id_or_token,
            OrganizationInvitation.deleted_at == None
        )
        res1 = await db.execute(stmt1)
        inv1 = res1.scalar_one_or_none()
        if inv1:
            return await org_service.reject_invitation(db, inv1.id, current_user)

        stmt2 = select(Invitation).where(
            Invitation.token == invite_id_or_token,
            Invitation.deleted_at == None
        )
        res2 = await db.execute(stmt2)
        inv2 = res2.scalar_one_or_none()
        if inv2:
            return await invite_service.reject_invitation(db, inv2.id, current_user)

        raise HTTPException(status_code=404, detail="Invitation not found")
