from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .multi_agent_orchestration_service import MultiAgentOrchestrationService

router = APIRouter(prefix="/multi-agent-orchestration", tags=["Multi-Agent Intelligence & Specialist Collaboration"])

class DecomposeTaskRequest(BaseModel):
    user_intent: str
    project_id: Optional[str] = None

class RouteTaskRequest(BaseModel):
    decomposition_id: str

class ExecuteSubtaskRequest(BaseModel):
    subtask_id: str
    agent_id: str
    input_payload: Dict[str, Any] = {}

class VerifySynthesizeRequest(BaseModel):
    subtask_outputs: List[Dict[str, Any]]

@router.get("/agents", status_code=status.HTTP_200_OK)
async def list_specialist_agents(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Registers and lists AgentDefinition records for specialist agents."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = MultiAgentOrchestrationService(db)
    return await service.register_and_get_agents(organization_id=org_id, user=current_user)

@router.post("/decompose", status_code=status.HTTP_200_OK)
async def decompose_task(
    req: DecomposeTaskRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Decomposes a complex objective into an AgentSubtask DAG."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    proj_uuid = UUID(req.project_id) if req.project_id else None
    service = MultiAgentOrchestrationService(db)
    return await service.decompose_task(
        user_intent=req.user_intent,
        project_id=proj_uuid,
        organization_id=org_id,
        user=current_user
    )

@router.post("/route", status_code=status.HTTP_200_OK)
async def route_and_delegate(
    req: RouteTaskRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Matches subtasks to specialists using AgentCapabilityRegistry & AgentRouter."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = MultiAgentOrchestrationService(db)
    return await service.route_and_delegate(decomposition_id=req.decomposition_id, organization_id=org_id, user=current_user)

@router.post("/execute-subtask", status_code=status.HTTP_200_OK)
async def execute_agent_subtask(
    req: ExecuteSubtaskRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Executes specialist subtask with input/output schema validation and correlation tracing."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = MultiAgentOrchestrationService(db)
    return await service.execute_agent_subtask(
        subtask_id=req.subtask_id,
        agent_id=req.agent_id,
        input_payload=req.input_payload,
        organization_id=org_id,
        user=current_user
    )

@router.post("/verify-synthesize", status_code=status.HTTP_200_OK)
async def verify_and_synthesize_outputs(
    req: VerifySynthesizeRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Runs Agent Verification Engine, identifies AgentConflicts on disagreement, and produces evidence-grounded brief."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = MultiAgentOrchestrationService(db)
    return await service.verify_and_synthesize_outputs(
        subtask_outputs=req.subtask_outputs,
        organization_id=org_id,
        user=current_user
    )
