from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .autonomous_service import AutonomousKnowledgeOperationsService

router = APIRouter(prefix="/operations/autonomous", tags=["Autonomous Knowledge Operations & Continuous Memory"])

class CreateRuleRequest(BaseModel):
    rule_name: str
    trigger_event: str
    scope: str
    action_name: str

class ReprocessRequest(BaseModel):
    entity_type: str
    entity_id: str

@router.get("/health", status_code=status.HTTP_200_OK)
async def get_operations_health(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve operational health overview across knowledge subsystems."""
    service = AutonomousKnowledgeOperationsService(db)
    return await service.get_operations_health(organization_id=org_id)

@router.get("/issues", status_code=status.HTTP_200_OK)
async def get_detected_issues_and_risks(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve detected stale documents, governance conflicts, documentation gaps, and project risks."""
    p_uuid = None
    if project_id:
        try:
            p_uuid = UUID(project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = AutonomousKnowledgeOperationsService(db)
    return await service.get_detected_issues_and_risks(user=current_user, organization_id=org_id, project_id=p_uuid)

@router.get("/digest", status_code=status.HTTP_200_OK)
async def get_knowledge_digest(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve daily/personal knowledge digest."""
    service = AutonomousKnowledgeOperationsService(db)
    return await service.get_knowledge_digest(user=current_user, organization_id=org_id)

@router.post("/rules", status_code=status.HTTP_200_OK)
async def create_automation_rule(
    req: CreateRuleRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a user-configured safe automation policy rule."""
    service = AutonomousKnowledgeOperationsService(db)
    return await service.create_automation_rule(
        user=current_user,
        organization_id=org_id,
        rule_name=req.rule_name,
        trigger_event=req.trigger_event,
        scope=req.scope,
        action_name=req.action_name
    )

@router.get("/rules", status_code=status.HTTP_200_OK)
async def get_automation_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve active automation rules."""
    service = AutonomousKnowledgeOperationsService(db)
    return await service.get_automation_rules(user=current_user)

@router.post("/rules/{rule_id}/toggle", status_code=status.HTTP_200_OK)
async def toggle_automation_rule(
    rule_id: str,
    enable: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Pause or resume an automation rule."""
    service = AutonomousKnowledgeOperationsService(db)
    return await service.toggle_automation_rule(rule_id=rule_id, enable=enable)

@router.post("/reprocess", status_code=status.HTTP_200_OK)
async def reprocess_entity(
    req: ReprocessRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Trigger background reprocessing for an entity idempotently."""
    try:
        e_uuid = UUID(req.entity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entity_id UUID format")

    service = AutonomousKnowledgeOperationsService(db)
    return await service.reprocess_entity(organization_id=org_id, entity_type=req.entity_type, entity_id=e_uuid)

@router.post("/reindex", status_code=status.HTTP_200_OK)
async def maintenance_reindex(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Trigger maintenance reindexing across Search, Graph, Timeline, and Governance."""
    service = AutonomousKnowledgeOperationsService(db)
    return await service.maintenance_reindex(organization_id=org_id)
