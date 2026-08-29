from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from ..core.database import get_db_session
from .schemas import WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse, WorkspaceMemberInvite, WorkspaceMemberResponse
from .service import WorkspaceService

router = APIRouter()

@router.post("/", response_model=WorkspaceResponse)
async def create_workspace(
    ws_in: WorkspaceCreate,
    req: Request,
    db: AsyncSession = Depends(get_db_session)
):
    org_id = UUID(str(req.state.org_id))
    user_id = UUID(str(req.state.user_id))
    service = WorkspaceService(db)
    return await service.create_workspace(ws_in.name, ws_in.slug, org_id, user_id)

@router.get("/", response_model=List[WorkspaceResponse])
async def list_workspaces(
    req: Request,
    db: AsyncSession = Depends(get_db_session)
):
    org_id = UUID(str(req.state.org_id))
    service = WorkspaceService(db)
    return await service.list_workspaces(org_id)

@router.get("/{id}", response_model=WorkspaceResponse)
async def get_workspace(
    id: UUID,
    req: Request,
    db: AsyncSession = Depends(get_db_session)
):
    org_id = UUID(str(req.state.org_id))
    service = WorkspaceService(db)
    return await service.get_workspace(id, org_id)

@router.patch("/{id}", response_model=WorkspaceResponse)
async def update_workspace(
    id: UUID,
    ws_in: WorkspaceUpdate,
    req: Request,
    db: AsyncSession = Depends(get_db_session)
):
    org_id = UUID(str(req.state.org_id))
    service = WorkspaceService(db)
    return await service.update_workspace(id, org_id, ws_in.name, ws_in.slug)

@router.delete("/{id}")
async def delete_workspace(
    id: UUID,
    req: Request,
    db: AsyncSession = Depends(get_db_session)
):
    org_id = UUID(str(req.state.org_id))
    service = WorkspaceService(db)
    await service.delete_workspace(id, org_id)
    return {"message": "Workspace deleted successfully"}

@router.post("/{id}/members")
async def invite_workspace_member(
    id: UUID,
    member_in: WorkspaceMemberInvite,
    req: Request,
    db: AsyncSession = Depends(get_db_session)
):
    org_id = UUID(str(req.state.org_id))
    service = WorkspaceService(db)
    await service.invite_member(id, org_id, member_in.email, member_in.role)
    return {"message": f"Successfully invited {member_in.email} to workspace"}

@router.get("/{id}/members", response_model=List[WorkspaceMemberResponse])
async def get_workspace_members(
    id: UUID,
    req: Request,
    db: AsyncSession = Depends(get_db_session)
):
    org_id = UUID(str(req.state.org_id))
    service = WorkspaceService(db)
    return await service.get_members(id, org_id)
