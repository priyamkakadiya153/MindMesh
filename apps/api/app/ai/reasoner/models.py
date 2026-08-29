import time
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

class ReasoningStatus(str, Enum):
    READY = "READY"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    AMBIGUOUS = "AMBIGUOUS"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"

class ReasoningMode(str, Enum):
    DIRECT = "DIRECT"
    SYNTHESIS = "SYNTHESIS"
    COMPARISON = "COMPARISON"
    TEMPORAL = "TEMPORAL"
    CAUSAL = "CAUSAL"
    DECISION = "DECISION"
    MULTI_SOURCE = "MULTI_SOURCE"
    ACTION_RESULT = "ACTION_RESULT"
    CALCULATION = "CALCULATION"

class AnswerReadiness(str, Enum):
    READY = "READY"
    READY_WITH_CAVEAT = "READY_WITH_CAVEAT"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    ACTION_IN_PROGRESS = "ACTION_IN_PROGRESS"
    ACTION_UNKNOWN = "ACTION_UNKNOWN"

class ClaimStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    HISTORICAL = "HISTORICAL"
    SUPERSEDED = "SUPERSEDED"

@dataclass
class ReasoningClaim:
    """Normalized Claim extracted from workspace evidence."""
    claim_id: str
    subject: str
    predicate: str
    object: str
    supporting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    conflicting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: str = "HIGH"
    status: ClaimStatus = ClaimStatus.SUPPORTED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "supporting_evidence": self.supporting_evidence,
            "conflicting_evidence": self.conflicting_evidence,
            "confidence": self.confidence,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status)
        }

@dataclass
class ReasoningRequest:
    """Request data for Reasoning & Context Orchestration."""
    request_id: uuid.UUID
    original_query: str
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    conversation_id: Optional[uuid.UUID] = None
    intent: Optional[Dict[str, Any]] = None
    conversation_context: Optional[Dict[str, Any]] = None
    evidence_set: Optional[Dict[str, Any]] = None
    resolved_entities: List[Dict[str, Any]] = field(default_factory=list)
    graph_context: Optional[Dict[str, Any]] = None
    action_results: List[Dict[str, Any]] = field(default_factory=list)
    reasoning_mode: ReasoningMode = ReasoningMode.DIRECT

@dataclass
class ReasoningResult:
    """Result of Reasoning & Context Orchestration."""
    request_id: uuid.UUID
    reasoning_status: ReasoningStatus
    conclusion: str
    supporting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    conflicting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    resolved_entities: List[Dict[str, Any]] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    calculations: Dict[str, Any] = field(default_factory=dict)
    action_effects: List[Dict[str, Any]] = field(default_factory=list)
    answer_readiness: AnswerReadiness = AnswerReadiness.READY
    reasoning_trace: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": str(self.request_id),
            "reasoning_status": self.reasoning_status.value if hasattr(self.reasoning_status, "value") else str(self.reasoning_status),
            "conclusion": self.conclusion,
            "supporting_evidence": self.supporting_evidence,
            "conflicting_evidence": self.conflicting_evidence,
            "resolved_entities": self.resolved_entities,
            "assumptions": self.assumptions,
            "uncertainties": self.uncertainties,
            "calculations": self.calculations,
            "action_effects": self.action_effects,
            "answer_readiness": self.answer_readiness.value if hasattr(self.answer_readiness, "value") else str(self.answer_readiness),
            "reasoning_trace": self.reasoning_trace
        }

@dataclass
class AnswerContext:
    """Hand-off contract object passed from AI-08 to AI-09 Answer Intelligence."""
    question: str
    conclusion: str
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    action_results: List[Dict[str, Any]] = field(default_factory=list)
    answer_readiness: AnswerReadiness = AnswerReadiness.READY

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "conclusion": self.conclusion,
            "evidence": self.evidence,
            "citations": self.citations,
            "uncertainties": self.uncertainties,
            "conflicts": self.conflicts,
            "entities": self.entities,
            "action_results": self.action_results,
            "answer_readiness": self.answer_readiness.value if hasattr(self.answer_readiness, "value") else str(self.answer_readiness)
        }
