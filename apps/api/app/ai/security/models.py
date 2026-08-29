import time
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

class TrustCategory(str, Enum):
    SYSTEM_TRUSTED = "SYSTEM_TRUSTED"
    APPLICATION_TRUSTED = "APPLICATION_TRUSTED"
    VERIFIED_STRUCTURED_DATA = "VERIFIED_STRUCTURED_DATA"
    AUTHORIZED_SOURCE = "AUTHORIZED_SOURCE"
    USER_CONTENT = "USER_CONTENT"
    RETRIEVED_CONTENT = "RETRIEVED_CONTENT"
    EXTERNAL_CONTENT = "EXTERNAL_CONTENT"
    TOOL_OUTPUT = "TOOL_OUTPUT"
    MODEL_GENERATED = "MODEL_GENERATED"
    UNTRUSTED = "UNTRUSTED"

class GroundingStatus(str, Enum):
    GROUNDED = "GROUNDED"
    PARTIALLY_GROUNDED = "PARTIALLY_GROUNDED"
    UNGROUNDED = "UNGROUNDED"
    CONFLICTING = "CONFLICTING"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    SECURITY_BLOCKED = "SECURITY_BLOCKED"
    PRIVACY_BLOCKED = "PRIVACY_BLOCKED"
    VALIDATION_FAILED = "VALIDATION_FAILED"

class ClaimType(str, Enum):
    FACT = "FACT"
    INFERENCE = "INFERENCE"
    CALCULATION = "CALCULATION"
    RECOMMENDATION = "RECOMMENDATION"
    ACTION_RESULT = "ACTION_RESULT"
    TEMPORAL = "TEMPORAL"
    COMPARATIVE = "COMPARATIVE"
    UNKNOWN = "UNKNOWN"

class PolicyDecision(str, Enum):
    ALLOW = "ALLOW"
    ALLOW_WITH_CAVEAT = "ALLOW_WITH_CAVEAT"
    REDACT = "REDACT"
    REQUIRE_CONFIRMATION = "REQUIRE_CONFIRMATION"
    DENY = "DENY"

class SecuritySeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class SecurityEventType(str, Enum):
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    CROSS_WORKSPACE_ATTEMPT = "CROSS_WORKSPACE_ATTEMPT"
    PROMPT_INJECTION_DETECTED = "PROMPT_INJECTION_DETECTED"
    SECRET_DETECTED = "SECRET_DETECTED"
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"
    INVALID_CITATION = "INVALID_CITATION"
    TOOL_POLICY_BLOCK = "TOOL_POLICY_BLOCK"
    RATE_LIMIT_TRIGGERED = "RATE_LIMIT_TRIGGERED"
    OUTPUT_REDACTED = "OUTPUT_REDACTED"

@dataclass
class AnswerClaim:
    """Extracted factual or logical claim from an answer."""
    claim_id: str
    text: str
    claim_type: ClaimType = ClaimType.FACT
    evidence_ids: List[str] = field(default_factory=list)
    confidence: float = 1.0
    status: str = "SUPPORTED"

@dataclass
class SecurityEvent:
    """Security audit event."""
    event_id: uuid.UUID
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    request_id: uuid.UUID
    event_type: SecurityEventType
    severity: SecuritySeverity
    timestamp: float
    resource_id: Optional[str] = None
    decision: PolicyDecision = PolicyDecision.DENY
    reason_code: str = "DEFAULT_SECURITY_BLOCK"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "user_id": str(self.user_id),
            "workspace_id": str(self.workspace_id),
            "request_id": str(self.request_id),
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "resource_id": self.resource_id,
            "decision": self.decision.value,
            "reason_code": self.reason_code
        }

@dataclass
class GroundingRequest:
    """Request data for Grounding & Security Evaluation."""
    request_id: uuid.UUID
    query: str
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    reasoning_result: Optional[Dict[str, Any]] = None
    answer_result: Optional[Dict[str, Any]] = None
    evidence_set: Optional[Dict[str, Any]] = None
    action_results: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class GroundingResult:
    """Result of Grounding & Security Evaluation."""
    status: GroundingStatus
    decision: PolicyDecision
    claims: List[AnswerClaim] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    redacted_content: Optional[str] = None
    security_events: List[SecurityEvent] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "decision": self.decision.value,
            "claims": [c.__dict__ for c in self.claims],
            "warnings": self.warnings,
            "redacted_content": self.redacted_content,
            "security_events": [e.to_dict() for e in self.security_events]
        }
