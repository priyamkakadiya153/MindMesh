from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional

from ..core.database import get_db_session
from ..auth.dependencies import get_current_user
from ..models.user import User
from ..authorization.organization_resolver import resolve_organization_id
from .schemas import (
    InvitationCreate, InvitationResponse, MemberDirectoryItem,
    MemberActionPayload, JoinRequestCreate, JoinRequestResponse, PermissionMatrixItem
)
from .service import MemberService, EnterpriseInvitationService, JoinRequestService

router = APIRouter()
member_service = MemberService()
invite_service = EnterpriseInvitationService()
join_service = JoinRequestService()

# Directory & Roster Endpoints
@router.get("", response_model=List[MemberDirectoryItem])
async def list_members_directory(
    workspace_id: Optional[UUID] = Query(None),
    project_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    return await member_service.list_directory(db, org_id, workspace_id, project_id, search, role)

@router.patch("/{user_id}")
async def update_member_action(
    user_id: UUID,
    payload: MemberActionPayload,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    return await member_service.update_member_action(db, current_user, user_id, org_id, payload)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    user_id: UUID,
    level: str = Query("organization"),
    workspace_id: Optional[UUID] = Query(None),
    project_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    await member_service.remove_member(db, current_user, user_id, org_id, level, workspace_id, project_id)

# Unified Invitations Endpoints
@router.post("/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def issue_invitation(
    invitation_in: InvitationCreate,
    current_user: User = Depends(get_current_user),
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    if not getattr(invitation_in, 'organization_id', None) and org_id:
        invitation_in.organization_id = org_id
    return await invite_service.issue_invitation(db, current_user, invitation_in)

@router.get("/invitations", response_model=List[InvitationResponse])
async def list_invitations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    invites = await invite_service.list_user_invitations(db, current_user.email)
    res = []
    for inv in invites:
        item = InvitationResponse.model_validate(inv)
        if inv.organization:
            item.org_name = inv.organization.name
        if inv.workspace:
            item.workspace_name = inv.workspace.name
        if inv.project:
            item.project_name = inv.project.name
        res.append(item)
    return res

@router.post("/invitations/{token_or_id}/accept")
async def accept_invitation(
    token_or_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await invite_service.accept_invitation(db, token_or_id, current_user)

@router.post("/invitations/{invite_id}/reject")
async def reject_invitation(
    invite_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await invite_service.reject_invitation(db, invite_id, current_user)

@router.delete("/invitations/{invite_id}", status_code=status.HTTP_200_OK)
async def cancel_invitation(
    invite_id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    return await invite_service.cancel_invitation(db, invite_id, org_id)

# Join Requests Endpoints
@router.post("/join-requests", response_model=JoinRequestResponse, status_code=status.HTTP_201_CREATED)
async def submit_join_request(
    request_in: JoinRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    req = await join_service.request_access(db, current_user, request_in)
    res = JoinRequestResponse.model_validate(req)
    res.username = current_user.username
    res.email = current_user.email
    return res

@router.get("/join-requests", response_model=List[JoinRequestResponse])
async def list_join_requests(
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    reqs = await join_service.list_join_requests(db, org_id)
    res = []
    for r in reqs:
        item = JoinRequestResponse.model_validate(r)
        if r.user:
            item.username = r.user.username
            item.email = r.user.email
        res.append(item)
    return res

@router.post("/join-requests/{request_id}/approve")
async def approve_join_request(
    request_id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    return await join_service.approve_request(db, request_id, org_id)

@router.post("/join-requests/{request_id}/reject")
async def reject_join_request(
    request_id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    return await join_service.reject_request(db, request_id, org_id)

# Permission Matrix Endpoint
@router.get("/permission-matrix", response_model=List[PermissionMatrixItem])
async def get_permission_matrix():
    matrix_data = [
        {"role_name": "owner", "permission_key": "org:manage", "is_granted": True},
        {"role_name": "owner", "permission_key": "workspace:manage", "is_granted": True},
        {"role_name": "owner", "permission_key": "project:manage", "is_granted": True},
        {"role_name": "admin", "permission_key": "org:invite", "is_granted": True},
        {"role_name": "admin", "permission_key": "workspace:manage", "is_granted": True},
        {"role_name": "manager", "permission_key": "project:manage", "is_granted": True},
        {"role_name": "contributor", "permission_key": "project:edit", "is_granted": True},
        {"role_name": "member", "permission_key": "project:view", "is_granted": True},
        {"role_name": "guest", "permission_key": "project:read_only", "is_granted": True},
        {"role_name": "viewer", "permission_key": "project:read_only", "is_granted": True},
    ]
    return [PermissionMatrixItem(**m) for m in matrix_data]
