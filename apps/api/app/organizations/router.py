from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from ..core.database import get_db_session
from ..auth.dependencies import get_current_user
from ..models.user import User
from .service import OrganizationService
from .schemas import (
    OrgCreate, OrgUpdate, OrgResponse, OrgSettingsSchema, OrgSettingsUpdate,
    MemberInvite, MemberRoleUpdate, MemberResponse, InvitationResponse
)

router = APIRouter()
org_service = OrganizationService()

@router.post("/", response_model=OrgResponse)
async def create_org(
    org_in: OrgCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    org = await org_service.create_organization(db, current_user.id, org_in)
    return org

@router.get("/", response_model=List[dict])
async def list_orgs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    orgs = await org_service.list_user_organizations(db, current_user.id)
    if not orgs:
        personal = await org_service.ensure_user_personal_org(db, current_user)
        orgs = await org_service.list_user_organizations(db, current_user.id)
    return orgs

@router.get("/current", response_model=OrgResponse)
async def get_current_org(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    org = await org_service.ensure_user_personal_org(db, current_user)
    return org

@router.get("/{org_id}", response_model=OrgResponse)
async def get_org(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    membership = await org_service.repo.get_membership(db, org_id, current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied")
    org = await org_service.get_organization(db, org_id)
    return org

@router.patch("/{org_id}", response_model=OrgResponse)
async def update_org(
    org_id: UUID,
    org_in: OrgUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    membership = await org_service.repo.get_membership(db, org_id, current_user.id)
    if not membership or membership.role.lower() not in ["owner", "admin", "super_admin", "org_admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    org = await org_service.update_organization(db, org_id, org_in)
    return org

@router.delete("/{org_id}")
async def delete_org(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    membership = await org_service.repo.get_membership(db, org_id, current_user.id)
    if not membership or membership.role.lower() not in ["owner", "super_admin"]:
        raise HTTPException(status_code=403, detail="Permission denied. Only organization owner can delete.")
    await org_service.delete_organization(db, org_id)
    return {"status": "ok", "message": "Organization deleted"}

@router.post("/{org_id}/switch", response_model=OrgResponse)
async def switch_org(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    org = await org_service.switch_organization(db, org_id, current_user)
    return org

@router.post("/{org_id}/leave")
async def leave_org(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    await org_service.leave_organization(db, org_id, current_user)
    return {"status": "ok", "message": "Successfully left the organization"}

@router.get("/{org_id}/settings", response_model=OrgSettingsSchema)
async def get_org_settings(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    membership = await org_service.repo.get_membership(db, org_id, current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied")
    return await org_service.get_settings(db, org_id)

@router.patch("/{org_id}/settings", response_model=OrgSettingsSchema)
async def update_org_settings(
    org_id: UUID,
    settings_in: OrgSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    membership = await org_service.repo.get_membership(db, org_id, current_user.id)
    if not membership or membership.role.lower() not in ["owner", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    return await org_service.update_settings(db, org_id, settings_in)

@router.post("/{org_id}/invite", response_model=InvitationResponse)
@router.post("/{org_id}/invitations", response_model=InvitationResponse)
async def invite_member(
    org_id: UUID,
    invite_in: MemberInvite,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    membership = await org_service.repo.get_membership(db, org_id, current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Permission denied. Only organization owners and admins can issue invitations.")
    
    user_role = (membership.role or '').lower()
    rel_role = (membership.role_rel.name if getattr(membership, 'role_rel', None) and hasattr(membership.role_rel, 'name') and membership.role_rel.name else '').lower()
    allowed_roles = ["owner", "admin", "super_admin", "org_admin"]
    if user_role not in allowed_roles and rel_role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Permission denied. Only organization owners and admins can issue invitations.")
        
    return await org_service.invite_member(db, org_id, invite_in, current_user.id, current_user_email=current_user.email)

@router.get("/{org_id}/invitations", response_model=List[InvitationResponse])
async def list_org_invitations(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    membership = await org_service.repo.get_membership(db, org_id, current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Permission denied")
    user_role = (membership.role or '').lower()
    rel_role = (membership.role_rel.name if getattr(membership, 'role_rel', None) and hasattr(membership.role_rel, 'name') and membership.role_rel.name else '').lower()
    allowed_roles = ["owner", "admin", "super_admin", "org_admin"]
    if user_role not in allowed_roles and rel_role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Permission denied")
    return await org_service.repo.list_org_invitations(db, org_id)

@router.get("/{org_id}/members", response_model=List[MemberResponse])
async def list_members(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    membership = await org_service.repo.get_membership(db, org_id, current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied")
    return await org_service.list_members(db, org_id)

@router.patch("/{org_id}/members/{member_id}", response_model=dict)
async def change_member_role(
    org_id: UUID,
    member_id: UUID,
    role_in: MemberRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    membership = await org_service.repo.get_membership(db, org_id, current_user.id)
    if not membership or membership.role.lower() not in ["owner", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    await org_service.change_role(db, org_id, member_id, role_in.role)
    return {"status": "ok", "message": "Member role updated successfully"}

@router.delete("/{org_id}/members/{member_id}")
async def remove_member(
    org_id: UUID,
    member_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    membership = await org_service.repo.get_membership(db, org_id, current_user.id)
    if not membership or membership.role.lower() not in ["owner", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    await org_service.remove_member(db, org_id, member_id)
    return {"status": "ok", "message": "Member removed successfully"}

