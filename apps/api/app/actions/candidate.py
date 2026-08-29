from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class IntentCategory(str, Enum):
    TASK_REQUEST = "TASK_REQUEST"
    REMINDER_INTENT = "REMINDER_INTENT"
    FOLLOW_UP = "FOLLOW_UP"
    DEADLINE = "DEADLINE"
    COMMITMENT = "COMMITMENT"
    REQUEST_TO_PERSON = "REQUEST_TO_PERSON"
    DELIVERABLE = "DELIVERABLE"
    MEETING_ACTION = "MEETING_ACTION"
    INFORMATION_ONLY = "INFORMATION_ONLY"
    GENERAL_CONVERSATION = "GENERAL_CONVERSATION"
    NO_ACTION = "NO_ACTION"
    COMPLETION_SIGNAL = "COMPLETION_SIGNAL"
    REVIEW_REQUEST = "REVIEW_REQUEST"
    FOLLOW_UP_REQUEST = "FOLLOW_UP_REQUEST"

class ActionType(str, Enum):
    TASK = "TASK"
    REMINDER = "REMINDER"
    FOLLOW_UP = "FOLLOW_UP"
    REVIEW = "REVIEW"
    VERIFY = "VERIFY"
    COMPLETION = "COMPLETION"
    DIRECT_MESSAGE = "DIRECT_MESSAGE"
    NO_ACTION = "NO_ACTION"

class UserResponsibilityRole(str, Enum):
    ASSIGNEE = "ASSIGNEE"
    REQUESTER = "REQUESTER"
    REVIEWER = "REVIEWER"
    OBSERVER = "OBSERVER"

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class CandidateStatus(str, Enum):
    DETECTED = "DETECTED"
    DISMISSED = "DISMISSED"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"

class ProvenanceContext(BaseModel):
    source_type: str = Field(default="DIRECT_MESSAGE", description="DIRECT_MESSAGE, GROUP_CONVERSATION, AI_CHAT, PROJECT, WORKSPACE")
    conversation_id: str
    message_id: Optional[str] = None
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    recipient_context: Optional[str] = None
    workspace_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ActionCandidate(BaseModel):
    """
    AUTO-01 & AUTO-10 Action Candidate Representation.
    Represents a detected role-aware actionable signal without taking downstream execution.
    """
    source: ProvenanceContext
    intent: IntentCategory = IntentCategory.NO_ACTION
    action_type: ActionType = ActionType.NO_ACTION
    candidate_type: str = "CREATE_TASK" # CREATE_TASK, CREATE_REMINDER, FOLLOW_UP, REVIEW, VERIFY, COMPLETION
    user_role: UserResponsibilityRole = UserResponsibilityRole.ASSIGNEE
    subject: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[str] = None # Original expression e.g. "next Monday"
    normalized_deadline: Optional[datetime] = None
    timezone: str = "UTC"
    assignee: Optional[str] = "UNKNOWN" # "Current speaker", named user, or "UNKNOWN"
    assignee_id: Optional[str] = None
    assignee_name: Optional[str] = None
    requester: Optional[str] = None
    requester_id: Optional[str] = None
    related_entities: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW
    requires_user_confirmation: bool = True
    personal_relevance: ConfidenceLevel = ConfidenceLevel.LOW
    status: CandidateStatus = CandidateStatus.DETECTED
    detected_action_hash: str = ""
    provenance: Dict[str, Any] = Field(default_factory=dict)
