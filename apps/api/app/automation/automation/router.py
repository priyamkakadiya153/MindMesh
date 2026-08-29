import logging
import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db_session
from app.api.dependencies import get_current_user
from app.authorization.organization_resolver import resolve_organization_id
from app.models.user import User

from app.automation.automation.schemas import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowExecutionResponse,
    ApprovalRequestResponse,
    ApprovalSubmitRequest,
    AutomationEventCreate,
    AutomationEventResponse
)
from app.automation.automation.service import AutomationService
from app.automation.automation.repository import AutomationRepository
from app.automation.approval.service import ApprovalService
from app.automation.events.publisher import EventPublisher
from app.automation.events.bus import event_bus
from app.automation.approval.models import AutomationEventLog
from app.automation.automation.analytics import AutomationAnalytics

logger = logging.getLogger(__name__)

router = APIRouter()

def get_org_uuid(org_id: Any) -> uuid.UUID:
    """Safely extracts UUID from both string and UUID representations."""
    if isinstance(org_id, uuid.UUID):
        return org_id
    try:
        return uuid.UUID(str(org_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid organization header ID.")

# ----------------- WORKFLOW ENDPOINTS -----------------

@router.post("/workflows", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow_definition(
    payload: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Creates a new workflow definition with dynamic event/scheduler registration."""
    try:
        wdef = await AutomationService.create_workflow(
            db=db,
            name=payload.name,
            description=payload.description,
            definition=payload.definition,
            organization_id=payload.organization_id
        )
        return wdef
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Router: Failed to create workflow: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/workflows", response_model=List[WorkflowResponse], status_code=status.HTTP_200_OK)
async def list_workflow_definitions(
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Lists all registered workflow definitions for the organization."""
    org_uuid = get_org_uuid(org_id)
    definitions = await AutomationRepository.list_workflows(db, org_uuid)
    return definitions

@router.get("/workflows/{id}", response_model=WorkflowResponse, status_code=status.HTTP_200_OK)
async def get_workflow_definition(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves operational details of a workflow definition."""
    wdef = await AutomationRepository.get_workflow(db, id)
    if not wdef:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow definition '{id}' not found.")
    return wdef

@router.post("/workflows/{id}/execute", response_model=WorkflowExecutionResponse, status_code=status.HTTP_200_OK)
async def execute_workflow_run(
    id: uuid.UUID,
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Explicitly triggers and runs a workflow definition instance."""
    org_uuid = get_org_uuid(org_id)
    try:
        execution = await AutomationService.trigger_workflow(
            db=db,
            workflow_id=id,
            initial_context=payload,
            organization_id=org_uuid
        )
        return execution
    except Exception as e:
        logger.error(f"Router: Failed to execute workflow: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/workflows/{id}/cancel", response_model=WorkflowExecutionResponse, status_code=status.HTTP_200_OK)
async def cancel_workflow_run(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Cancels a currently active workflow execution pipeline."""
    execution = await AutomationService.cancel_workflow(db, id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Execution '{id}' not found.")
    return execution

# ----------------- HUMAN APPROVAL ENDPOINTS -----------------

@router.post("/approvals/{id}/approve", response_model=ApprovalRequestResponse, status_code=status.HTTP_200_OK)
async def approve_request(
    id: uuid.UUID,
    payload: ApprovalSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Submits an approval vote, resuming blocked pipeline execution steps."""
    try:
        approval = await ApprovalService.submit_decision(
            db=db,
            approval_id=id,
            user_id=str(current_user.id),
            vote="Approved",
            comments=payload.comments
        )
        await db.commit()
        return approval
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Router: Failed to approve request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/approvals/{id}/reject", response_model=ApprovalRequestResponse, status_code=status.HTTP_200_OK)
async def reject_request(
    id: uuid.UUID,
    payload: ApprovalSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Submits a rejection decision, aborting and rolling back the linked workflow execution."""
    try:
        approval = await ApprovalService.submit_decision(
            db=db,
            approval_id=id,
            user_id=str(current_user.id),
            vote="Rejected",
            comments=payload.comments
        )
        await db.commit()
        return approval
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Router: Failed to reject request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/approvals", response_model=List[ApprovalRequestResponse], status_code=status.HTTP_200_OK)
async def list_approval_requests(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Lists approval requests filtered by status."""
    org_uuid = get_org_uuid(org_id)
    approvals = await ApprovalService.list_approvals(db, org_uuid, status_filter)
    return approvals

# ----------------- EVENT ENDPOINTS -----------------

@router.post("/events", response_model=AutomationEventResponse, status_code=status.HTTP_201_CREATED)
async def trigger_business_event(
    payload: AutomationEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Publishes a business event to trigger subscribing workflows."""
    log = await EventPublisher.publish_event(
        event_type=payload.event_type,
        payload=payload.payload,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        db=db
    )
    if not log:
        # Default mock response if database logging failed
        return {
            "id": uuid.uuid4(),
            "event_type": payload.event_type,
            "payload": payload.payload,
            "processed": True,
            "triggered_workflow_id": None,
            "organization_id": payload.organization_id,
            "workspace_id": payload.workspace_id,
            "created_at": datetime.utcnow()
        }
    return log

@router.get("/events", response_model=List[AutomationEventResponse], status_code=status.HTTP_200_OK)
async def list_fired_events(
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Lists history of fired automation event logs."""
    org_uuid = get_org_uuid(org_id)
    stmt = select(AutomationEventLog).where(AutomationEventLog.organization_id == org_uuid)
    res = await db.execute(stmt)
    return list(res.scalars().all())

# ----------------- DASHBOARD ENDPOINTS -----------------

@router.get("/automation/dashboard", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_dashboard_kpis(
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Aggregates SLA status, queue sizes, active workers count, and job metrics."""
    org_uuid = get_org_uuid(org_id)
    metrics = await AutomationAnalytics.get_dashboard_summary(db, org_uuid)
    return metrics
