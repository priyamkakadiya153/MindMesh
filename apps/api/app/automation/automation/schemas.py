from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, List, Optional

class WorkflowCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    definition: Dict[str, Any] = Field(...)  # Steps structure mapping
    organization_id: UUID

class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str]
    definition: Dict[str, Any]
    version: int
    organization_id: UUID
    workspace_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

class WorkflowExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_id: UUID
    status: str
    context: Dict[str, Any]
    current_step_index: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]
    organization_id: UUID
    workspace_id: Optional[UUID]
    created_at: datetime

class ApprovalRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_execution_id: Optional[UUID]
    step_name: Optional[str]
    title: str
    description: Optional[str]
    status: str
    assigned_approver: Optional[str]
    policy_type: str
    approvers_voted: Dict[str, Any]
    decision_by: Optional[str]
    decision_at: Optional[datetime]
    comments: Optional[str]
    escalated_to: Optional[str]
    delegated_to: Optional[str]
    escalated_at: Optional[datetime]
    sla_limit_hours: Optional[int]
    organization_id: UUID
    workspace_id: Optional[UUID]
    created_at: datetime

class ApprovalSubmitRequest(BaseModel):
    vote: str = Field(..., pattern="^(Approved|Rejected)$")
    comments: Optional[str] = None

class AutomationEventCreate(BaseModel):
    event_type: str = Field(..., max_length=100)
    payload: Dict[str, Any] = Field(default_factory=dict)
    organization_id: UUID
    workspace_id: Optional[UUID] = None

class AutomationEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    payload: Dict[str, Any]
    processed: bool
    triggered_workflow_id: Optional[UUID]
    organization_id: UUID
    workspace_id: Optional[UUID]
    created_at: datetime
