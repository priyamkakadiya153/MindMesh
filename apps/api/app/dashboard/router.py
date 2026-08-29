from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from ..core.database import get_db_session
from ..auth.dependencies import get_current_user
from ..models.user import User
from ..authorization.organization_resolver import resolve_organization_id
from .schemas import DashboardResponse
from .service import DashboardService

router = APIRouter()

@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    workspace_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = DashboardService(db)
    return await service.get_dashboard(
        user_id=current_user.id,
        org_id=org_id,
        workspace_id=workspace_id
    )

@router.get("/widgets")
async def get_dashboard_widgets():
    return {
        "widgets": [
            {"id": "recent_projects", "name": "Recent Projects", "enabled": True, "col_span": 1},
            {"id": "recent_documents", "name": "Recent Documents", "enabled": True, "col_span": 2},
            {"id": "recent_chats", "name": "Recent Chats", "enabled": True, "col_span": 1},
            {"id": "activity_feed", "name": "Activity Feed Log", "enabled": True, "col_span": 1},
            {"id": "notifications", "name": "Notifications", "enabled": True, "col_span": 1},
            {"id": "ai_insights", "name": "AI Insights", "enabled": True, "col_span": 1},
            {"id": "favorites", "name": "Favorites Bookmarks", "enabled": True, "col_span": 1}
        ]
    }

@router.get("/summary")
async def get_dashboard_summary(
    workspace_id: Optional[UUID] = None,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = DashboardService(db)
    stats = await service.aggregator.aggregate_stats(org_id, workspace_id)
    return {
        "organization_id": org_id,
        "statistics": stats
    }

@router.get("/recent-projects")
async def get_recent_projects(
    workspace_id: Optional[UUID] = None,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = DashboardService(db)
    projects = await service.get_recent_projects(org_id, workspace_id)
    return {"recent_projects": projects}

@router.get("/recent-documents")
async def get_recent_documents(
    workspace_id: Optional[UUID] = None,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = DashboardService(db)
    docs = await service.get_recent_documents(org_id, workspace_id)
    return {"recent_documents": docs}

@router.get("/recent-chats")
async def get_recent_chats(
    workspace_id: Optional[UUID] = None,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = DashboardService(db)
    chats = await service.get_recent_chats(org_id, workspace_id)
    return {"recent_chats": chats}

@router.get("/ai-summary")
async def get_ai_summary(
    workspace_id: Optional[UUID] = None,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    service = DashboardService(db)
    summary = await service.get_ai_summary(org_id, workspace_id)
    return {"ai_summary": summary}

