import time
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ToolCapability(str, Enum):
    READ = "READ"
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SEARCH = "SEARCH"
    EXPORT = "EXPORT"
    COMMUNICATE = "COMMUNICATE"

class SideEffect(str, Enum):
    READ_ONLY = "READ_ONLY"
    LOW_IMPACT_WRITE = "LOW_IMPACT_WRITE"
    HIGH_IMPACT_WRITE = "HIGH_IMPACT_WRITE"
    DESTRUCTIVE = "DESTRUCTIVE"

class ExecutionStatus(str, Enum):
    PLANNED = "PLANNED"
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
    AUTHORIZED = "AUTHORIZED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"
    PARTIALLY_SUCCEEDED = "PARTIALLY_SUCCEEDED"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"

class ConfirmationLevel(str, Enum):
    NONE = "NONE"
    OPTIONAL = "OPTIONAL"
    REQUIRED = "REQUIRED"

@dataclass
class ToolDefinition:
    """Explicit Schema & Metadata for a Registered Tool."""
    tool_id: str
    name: str
    description: str
    version: str = "1.0.0"
    input_schema: Dict[str, Any] = field(default_factory=dict)   # {param_name: {"type": str/int/bool, "required": bool, "enum": [...]}}
    output_schema: Dict[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    permissions: List[str] = field(default_factory=list)        # e.g. ["tasks:create"]
    side_effects: SideEffect = SideEffect.READ_ONLY
    idempotency_support: bool = True
    timeout: float = 10.0
    handler: Optional[Callable] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "input_schema": self.input_schema,
            "risk_level": self.risk_level.value if hasattr(self.risk_level, "value") else str(self.risk_level),
            "permissions": self.permissions,
            "side_effects": self.side_effects.value if hasattr(self.side_effects, "value") else str(self.side_effects),
            "idempotency_support": self.idempotency_support,
            "timeout": self.timeout
        }

@dataclass
class ActionRequest:
    """Action Intent Request."""
    request_id: uuid.UUID
    conversation_id: Optional[uuid.UUID]
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    intent: str
    action_type: str
    target_type: Optional[str] = None
    target_entity_id: Optional[uuid.UUID] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    requires_confirmation: bool = False
    confirmation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": str(self.request_id),
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "user_id": str(self.user_id),
            "workspace_id": str(self.workspace_id),
            "intent": self.intent,
            "action_type": self.action_type,
            "target_type": self.target_type,
            "target_entity_id": str(self.target_entity_id) if self.target_entity_id else None,
            "parameters": self.parameters,
            "risk_level": self.risk_level.value if hasattr(self.risk_level, "value") else str(self.risk_level),
            "requires_confirmation": self.requires_confirmation,
            "confirmation_id": self.confirmation_id
        }

@dataclass
class ActionStep:
    """Individual Step in an Action Plan."""
    step_id: str
    tool_id: str
    action: str
    target: Optional[str]
    parameters: Dict[str, Any] = field(default_factory=dict)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    status: ExecutionStatus = ExecutionStatus.PLANNED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "tool_id": self.tool_id,
            "action": self.action,
            "target": self.target,
            "parameters": self.parameters,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status)
        }

@dataclass
class ActionPlan:
    """Multi-Step Action Execution Plan."""
    plan_id: uuid.UUID
    steps: List[ActionStep] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    confirmation_required: bool = False
    confirmation_prompt: Optional[str] = None
    confirmation_id: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.LOW
    status: ExecutionStatus = ExecutionStatus.PLANNED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": str(self.plan_id),
            "steps": [s.to_dict() for s in self.steps],
            "dependencies": self.dependencies,
            "confirmation_required": self.confirmation_required,
            "confirmation_prompt": self.confirmation_prompt,
            "confirmation_id": self.confirmation_id,
            "risk_level": self.risk_level.value if hasattr(self.risk_level, "value") else str(self.risk_level),
            "status": self.status.value if hasattr(self.status, "value") else str(self.status)
        }

@dataclass
class ToolResult:
    """Normalized Output from Tool Execution."""
    tool_call_id: str
    status: ExecutionStatus
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    affected_entities: List[str] = field(default_factory=list)
    verification_status: str = "VERIFIED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_call_id": self.tool_call_id,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "data": self.data,
            "error": self.error,
            "affected_entities": self.affected_entities,
            "verification_status": self.verification_status
        }

@dataclass
class ActionAuditRecord:
    """Immutable Audit Log Record for AI Action Executions."""
    execution_id: uuid.UUID
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    action_type: str
    tool_id: str
    target: Optional[str]
    parameters_summary: Dict[str, Any]
    status: ExecutionStatus
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": str(self.execution_id),
            "user_id": str(self.user_id),
            "workspace_id": str(self.workspace_id),
            "action_type": self.action_type,
            "tool_id": self.tool_id,
            "target": self.target,
            "parameters_summary": self.parameters_summary,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "timestamp": self.timestamp
        }
