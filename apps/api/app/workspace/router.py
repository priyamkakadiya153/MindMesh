from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from ..core.database import get_db_session
from ..auth.dependencies import get_current_user
from ..models.user import User
from ..authorization.organization_resolver import resolve_organization_id
from .schemas import (
    WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse,
    WorkspaceSettingsSchema, WorkspaceSettingsUpdate,
    WorkspaceMemberInvite, WorkspaceMemberResponse
)
from .service import WorkspaceService
from .dependencies import get_current_workspace
from .models import Workspace

router = APIRouter()

@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    ws_in: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = WorkspaceService(db)
    return await service.create_workspace(
        name=ws_in.name,
        org_id=org_id,
        user_id=current_user.id,
        description=ws_in.description,
        icon=ws_in.icon,
        color=ws_in.color
    )

@router.get("/", response_model=List[WorkspaceResponse])
async def list_workspaces(
    include_archived: bool = True,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = WorkspaceService(db)
    return await service.list_workspaces(org_id, current_user.id, include_archived)

@router.get("/current", response_model=WorkspaceResponse)
async def get_current_workspace_endpoint(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = WorkspaceService(db)
    if current_user.current_workspace_id:
        try:
            return await service.get_workspace(current_user.current_workspace_id, org_id)
        except Exception:
            pass

    workspaces = await service.list_workspaces(org_id, current_user.id, include_archived=False)
    if not workspaces:
        # Create default workspace if none
        default_ws = await service.create_workspace(
            name="General",
            org_id=org_id,
            user_id=current_user.id,
            description="Default workspace",
            color="#3B82F6"
        )
        current_user.current_workspace_id = default_ws.id
        db.add(current_user)
        await db.commit()
        return default_ws

    current_user.current_workspace_id = workspaces[0].id
    db.add(current_user)
    await db.commit()
    return workspaces[0]

@router.get("/{id}", response_model=WorkspaceResponse)
async def get_workspace(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = WorkspaceService(db)
    return await service.get_workspace(id, org_id)

@router.post("/{id}/switch", response_model=WorkspaceResponse)
async def switch_workspace(
    id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = WorkspaceService(db)
    ws = await service.get_workspace(id, org_id)
    current_user.current_workspace_id = ws.id
    db.add(current_user)
    await db.commit()
    return ws

@router.patch("/{id}", response_model=WorkspaceResponse)
async def update_workspace(
    id: UUID,
    ws_in: WorkspaceUpdate,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = WorkspaceService(db)
    return await service.update_workspace(
        id=id,
        org_id=org_id,
        name=ws_in.name,
        description=ws_in.description,
        icon=ws_in.icon,
        color=ws_in.color
    )

@router.get("/{id}/settings", response_model=WorkspaceSettingsSchema)
async def get_workspace_settings(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = WorkspaceService(db)
    return await service.get_settings(id, org_id)

@router.patch("/{id}/settings", response_model=WorkspaceSettingsSchema)
async def update_workspace_settings(
    id: UUID,
    settings_in: WorkspaceSettingsUpdate,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = WorkspaceService(db)
    return await service.update_settings(id, org_id, settings_in.dict(exclude_unset=True))

@router.post("/{id}/archive", response_model=WorkspaceResponse)
async def archive_workspace(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = WorkspaceService(db)
    return await service.archive_workspace(id, org_id)

@router.post("/{id}/restore", response_model=WorkspaceResponse)
async def restore_workspace(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = WorkspaceService(db)
    return await service.restore_workspace(id, org_id)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = WorkspaceService(db)
    await service.delete_workspace(id, org_id, soft=True)

@router.get("/{id}/members", response_model=List[WorkspaceMemberResponse])
async def list_workspace_members(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = WorkspaceService(db)
    return await service.get_workspace_members(id, org_id)

@router.post("/{id}/members", response_model=dict)
async def add_workspace_member(
    id: UUID,
    member_in: WorkspaceMemberInvite,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = WorkspaceService(db)
    # Find user by email
    from ..models.user import User
    from sqlalchemy import select
    user_res = await db.execute(select(User).where(User.email == member_in.email, User.deleted_at.is_(None)))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await service.invite_workspace_member(id, org_id, user.id, member_in.role)
    return {"status": "ok", "message": f"Successfully added {user.email} to workspace"}

@router.delete("/{id}/members/{user_id}")
async def remove_workspace_member(
    id: UUID,
    user_id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = WorkspaceService(db)
    await service.remove_workspace_member(id, org_id, user_id)
    return {"status": "ok", "message": "Workspace member removed"}

