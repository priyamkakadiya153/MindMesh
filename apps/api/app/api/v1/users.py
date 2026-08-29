from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import selectinload

from ...core.database import get_db_session
from ..dependencies import get_current_user
from ...models.user import User
from ...models.organization import Organization
from ...models.organization_member import OrganizationMember
from ...workspace.models import Workspace, WorkspaceMember
from ...auth.service import AuthService
from ...auth.schemas import ChangePasswordRequest, ChangeEmailRequest, ChangeMobileRequest
from ...auth.utils import normalize_phone_number, validate_and_normalize_phone_number

router = APIRouter()
auth_service = AuthService()

class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    theme: Optional[str] = None

class AvatarUpdate(BaseModel):
    avatar_url: str

class UpdateCurrentOrg(BaseModel):
    organization_id: UUID

class UpdateCurrentWorkspace(BaseModel):
    workspace_id: UUID

@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(OrganizationMember).where(OrganizationMember.user_id == current_user.id)
    res = await db.execute(stmt)
    memberships = res.scalars().all()
    
    org_list = []
    for m in memberships:
        org_res = await db.execute(select(Organization).where(Organization.id == m.organization_id))
        org = org_res.scalar_one_or_none()
        if org:
            org_list.append({
                "organization_id": str(org.id),
                "name": org.name,
                "slug": org.slug,
                "role": m.role if m.role else "MEMBER",
                "logo_url": org.logo_url,
                "description": org.description
            })

    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "phone_number": current_user.phone_number,
        "avatar_url": current_user.avatar_url,
        "bio": current_user.bio,
        "timezone": current_user.timezone or "UTC",
        "language": current_user.language or "en",
        "theme": current_user.theme or "dark",
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "is_phone_verified": current_user.is_phone_verified,
        "two_factor_enabled": current_user.two_factor_enabled,
        "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        "organizations": org_list,
        "current_organization_id": str(current_user.current_organization_id) if current_user.current_organization_id else None,
        "current_workspace_id": str(current_user.current_workspace_id) if current_user.current_workspace_id else None
    }

@router.put("/me")
@router.patch("/me")
async def update_profile(
    profile_in: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    if profile_in.username is not None and profile_in.username != current_user.username:
        # Check duplicate username
        existing = await auth_service.repo.get_user_by_username(db, profile_in.username)
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken.")
        current_user.username = profile_in.username

    if profile_in.first_name is not None:
        current_user.first_name = profile_in.first_name
    if profile_in.last_name is not None:
        current_user.last_name = profile_in.last_name
    if profile_in.phone_number is not None:
        norm_phone = normalize_phone_number(profile_in.phone_number)
        if norm_phone and norm_phone != current_user.phone_number:
            existing_phone = await auth_service.repo.get_user_by_phone_number(db, norm_phone)
            if existing_phone and existing_phone.id != current_user.id:
                raise HTTPException(status_code=400, detail="This mobile number is already registered.")
        current_user.phone_number = norm_phone
    if profile_in.bio is not None:
        current_user.bio = profile_in.bio
    if profile_in.timezone is not None:
        current_user.timezone = profile_in.timezone
    if profile_in.language is not None:
        current_user.language = profile_in.language
    if profile_in.theme is not None:
        current_user.theme = profile_in.theme

    db.add(current_user)
    await auth_service.log_audit_event(db, current_user.id, "user.profile_updated")
    await db.commit()
    return {"status": "ok", "message": "Profile updated successfully"}

@router.patch("/avatar")
async def update_avatar(
    body: AvatarUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    current_user.avatar_url = body.avatar_url
    db.add(current_user)
    await auth_service.log_audit_event(db, current_user.id, "user.avatar_updated")
    await db.commit()
    return {"status": "ok", "avatar_url": current_user.avatar_url}

@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    await auth_service.change_password(db, current_user, body.current_password, body.new_password)
    return {"status": "ok", "message": "Password changed successfully."}

@router.post("/change-email")
async def change_email(
    body: ChangeEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    existing = await auth_service.repo.get_user_by_email(db, body.new_email)
    if existing:
        raise HTTPException(status_code=400, detail="Email is already in use.")
    current_user.email = body.new_email
    current_user.is_verified = False
    db.add(current_user)
    await auth_service.email_service.send_email_verification(db, current_user)
    await auth_service.log_audit_event(db, current_user.id, "user.email_changed", details={"new_email": body.new_email})
    await db.commit()
    return {"status": "ok", "message": "Email updated. Verification link sent to new email address."}

@router.post("/change-mobile")
async def change_mobile(
    body: ChangeMobileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    norm_phone = validate_and_normalize_phone_number(body.new_phone_number)
    if norm_phone != current_user.phone_number:
        existing = await auth_service.repo.get_user_by_phone_number(db, norm_phone)
        if existing and existing.id != current_user.id:
            raise HTTPException(status_code=400, detail="This mobile number is already registered.")
    current_user.phone_number = norm_phone
    current_user.is_phone_verified = False
    db.add(current_user)
    await auth_service.otp_service.request_phone_otp(db, norm_phone)
    await auth_service.log_audit_event(db, current_user.id, "user.mobile_changed", details={"new_phone": norm_phone})
    await db.commit()
    return {"status": "ok", "message": "Mobile number updated. OTP sent for verification."}

@router.get("/export-data")
async def export_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    data = await auth_service.export_user_data(db, current_user)
    return data

@router.delete("/me")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    await auth_service.delete_account(db, current_user)
    return {"status": "ok", "message": "Account has been deleted."}

@router.patch("/current-organization")
async def update_current_org(
    body: UpdateCurrentOrg,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(OrganizationMember).where(
        OrganizationMember.organization_id == body.organization_id,
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.deleted_at == None
    )
    res = await db.execute(stmt)
    membership = res.scalar_one_or_none()
    if not membership:
        raise HTTPException(
            status_code=403,
            detail="You don't have access to this organization."
        )
    
    current_user.current_organization_id = body.organization_id
    
    ws_stmt = select(Workspace).where(
        Workspace.organization_id == body.organization_id,
        Workspace.is_active == True,
        Workspace.deleted_at == None
    ).order_by(Workspace.is_default.desc(), Workspace.created_at.asc())
    ws_res = await db.execute(ws_stmt)
    first_ws = ws_res.scalars().first()
    if first_ws:
        current_user.current_workspace_id = first_ws.id
    else:
        current_user.current_workspace_id = None
        
    db.add(current_user)
    await db.commit()
    return {
        "status": "ok",
        "current_organization_id": str(current_user.current_organization_id),
        "current_workspace_id": str(current_user.current_workspace_id) if current_user.current_workspace_id else None
    }

@router.patch("/current-workspace")
async def update_current_workspace(
    body: UpdateCurrentWorkspace,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(Workspace).where(
        Workspace.id == body.workspace_id,
        Workspace.is_active == True,
        Workspace.deleted_at == None
    )
    res = await db.execute(stmt)
    workspace = res.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found.")
        
    ws_mem_stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == body.workspace_id,
        WorkspaceMember.user_id == current_user.id,
        WorkspaceMember.is_active == True
    )
    ws_mem_res = await db.execute(ws_mem_stmt)
    ws_membership = ws_mem_res.scalar_one_or_none()
    if not ws_membership:
        raise HTTPException(status_code=403, detail="You don't have access to this workspace.")
        
    current_user.current_workspace_id = body.workspace_id
    current_user.current_organization_id = workspace.organization_id
    db.add(current_user)
    await db.commit()
    
    return {
        "status": "ok",
        "current_organization_id": str(current_user.current_organization_id),
        "current_workspace_id": str(current_user.current_workspace_id)
    }
