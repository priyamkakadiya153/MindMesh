from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .governance_engine_service import GovernanceEngineService

router = APIRouter(prefix="/governance-policies", tags=["Enterprise Governance, Policy Control & Guardrails"])

class CreatePolicyRequest(BaseModel):
    name: str
    description: str
    category: str
    scope: str = "ORGANIZATION"
    effect: str = "REQUIRE_APPROVAL"
    rules: Dict[str, Any]

class EvaluatePolicyRequest(BaseModel):
    action: str # TOOL_CALL, AGENT_EXECUTION, EXTERNAL_AI_PROCESSING, DATA_EXPORT
    data_classification: str = "Confidential" # Public, Internal, Confidential, Restricted
    target_resource: str
    context: Dict[str, Any] = {}

class ExceptionRequest(BaseModel):
    policy_id: str
    justification: str
    duration_hours: int = 24

class SimulationRequest(BaseModel):
    proposed_policy_rule: str

@router.get("/list", status_code=status.HTTP_200_OK)
async def list_policies(
    query: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Lists active, draft, and expired Policy definitions by category."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = GovernanceEngineService(db)
    return await service.list_policies(query=query, category=category, organization_id=org_id, user=current_user)

@router.post("/create", status_code=status.HTTP_200_OK)
async def create_or_update_policy(
    req: CreatePolicyRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Creates policy draft with structured rules, precedence, effect, and effective date."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = GovernanceEngineService(db)
    return await service.create_or_update_policy(
        name=req.name,
        description=req.description,
        category=req.category,
        scope=req.scope,
        effect=req.effect,
        rules=req.rules,
        organization_id=org_id,
        user=current_user
    )

@router.post("/evaluate", status_code=status.HTTP_200_OK)
async def evaluate_policy(
    req: EvaluatePolicyRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Pre-action evaluation for tool calls, agent execution, external AI processing, and data exports."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = GovernanceEngineService(db)
    return await service.evaluate_policy(
        action=req.action,
        data_classification=req.data_classification,
        target_resource=req.target_resource,
        context=req.context,
        organization_id=org_id,
        user=current_user
    )

@router.post("/exceptions/request", status_code=status.HTTP_200_OK)
async def request_policy_exception(
    req: ExceptionRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Grants temporary, narrowly-scoped PolicyException with approval requirement and explicit expiration timestamp."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = GovernanceEngineService(db)
    return await service.request_policy_exception(
        policy_id=req.policy_id,
        justification=req.justification,
        duration_hours=req.duration_hours,
        organization_id=org_id,
        user=current_user
    )

@router.post("/simulate", status_code=status.HTTP_200_OK)
async def simulate_policy_impact(
    req: SimulationRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Runs simulation engine on hypothetical scenario, returning evaluation results and impact warnings."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = GovernanceEngineService(db)
    return await service.simulate_policy_impact(proposed_policy_rule=req.proposed_policy_rule, organization_id=org_id, user=current_user)

@router.get("/audit", status_code=status.HTTP_200_OK)
async def list_governance_audit(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Returns governance audit events, policy violations, and compliance indicators."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = GovernanceEngineService(db)
    return await service.list_governance_audit(organization_id=org_id, user=current_user)
