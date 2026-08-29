from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .learning_service import OrganizationalLearningService

router = APIRouter(prefix="/learning", tags=["Organizational Learning & Knowledge Evolution"])

class ConfirmInsightRequest(BaseModel):
    insight_id: str

@router.get("/insights", status_code=status.HTTP_200_OK)
async def detect_insights(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve detected organizational learning insights."""
    p_uuid = None
    if project_id:
        try:
            p_uuid = UUID(project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = OrganizationalLearningService(db)
    return await service.detect_insights(user=current_user, organization_id=org_id, project_id=p_uuid)

@router.get("/evolution/{entity_type}/{entity_id}", status_code=status.HTTP_200_OK)
async def get_knowledge_evolution(
    entity_type: str,
    entity_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Trace historical evolution of a decision or document."""
    try:
        e_uuid = UUID(entity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entity_id UUID format")

    service = OrganizationalLearningService(db)
    return await service.get_knowledge_evolution(entity_type=entity_type, entity_id=e_uuid)

@router.post("/insights/confirm", status_code=status.HTTP_200_OK)
async def confirm_insight(
    req: ConfirmInsightRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Confirm a derived insight as a Governed Organizational Insight."""
    service = OrganizationalLearningService(db)
    return await service.confirm_insight(insight_id=req.insight_id, user=current_user)

@router.post("/insights/dismiss", status_code=status.HTTP_200_OK)
async def dismiss_insight(
    req: ConfirmInsightRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Dismiss an insight."""
    service = OrganizationalLearningService(db)
    return await service.dismiss_insight(insight_id=req.insight_id, user=current_user)

@router.get("/reuse-suggestions", status_code=status.HTTP_200_OK)
async def get_knowledge_reuse_suggestions(
    query: str = Query("Authentication"),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Recommend relevant historical decisions/projects clearly labeled as Historical Reference."""
    service = OrganizationalLearningService(db)
    return await service.get_knowledge_reuse_suggestions(user=current_user, organization_id=org_id, query=query)

@router.post("/rebuild-insights", status_code=status.HTTP_200_OK)
async def rebuild_insights(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Idempotently reconstruct derived insights from primary database records."""
    service = OrganizationalLearningService(db)
    return await service.rebuild_insights(organization_id=org_id)
