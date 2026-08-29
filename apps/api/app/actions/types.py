from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class ActionIntentType(str, Enum):
    CREATE_TASK = "CREATE_TASK"
    UPDATE_TASK = "UPDATE_TASK"
    ASSIGN_TASK = "ASSIGN_TASK"
    COMPLETE_TASK = "COMPLETE_TASK"
    CREATE_REMINDER = "CREATE_REMINDER"
    CREATE_DECISION = "CREATE_DECISION"
    SEND_DIRECT_MESSAGE = "SEND_DIRECT_MESSAGE"
    CREATE_AUTOMATION = "CREATE_AUTOMATION"
    PAUSE_AUTOMATION = "PAUSE_AUTOMATION"
    RESUME_AUTOMATION = "RESUME_AUTOMATION"
    CANCEL_AUTOMATION = "CANCEL_AUTOMATION"
    UPDATE_AUTOMATION = "UPDATE_AUTOMATION"
    DELETE_DOCUMENT = "DELETE_DOCUMENT"

class ActionStatus(str, Enum):
    DETECTED = "DETECTED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    READY_FOR_CONFIRMATION = "READY_FOR_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"

class ActionResultStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"

class ActionProposal(BaseModel):
    proposal_id: str
    intent_type: ActionIntentType
    title: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    workspace_id: Optional[str] = None
    user_id: Optional[str] = None
    confirmation_required: bool = True
    status: ActionStatus = ActionStatus.READY_FOR_CONFIRMATION
    clarification_prompt: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ActionResult(BaseModel):
    status: ActionResultStatus
    action_type: ActionIntentType
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    message: str
    error_code: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    executed_at: datetime = Field(default_factory=datetime.utcnow)

class ActionConfirmRequest(BaseModel):
    proposal_id: str
    intent_type: ActionIntentType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    confirm: bool = True
    workspace_id: Optional[str] = None
